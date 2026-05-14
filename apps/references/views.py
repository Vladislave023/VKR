from __future__ import annotations

import os
import tempfile
from typing import Callable

from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .adapters.kug_adapter import parse_kug
from .adapters.sr_adapter import parse_sr
from .models import Department, EducationLevel, ImportLog, Institute, Program, Specialty
from .services import ImportStats, save_kug_records, save_sr_records


def _status_for_import(created: int, skipped: int, error_count: int) -> str:
    """Return ImportLog status for collected counters."""
    if error_count and not created and not skipped:
        return "error"
    if error_count:
        return "partial"
    return "ok"


def _save_uploaded_xlsx(uploaded_file: UploadedFile) -> str:
    """Save an uploaded xlsx file to a temporary file and return its path."""
    suffix = os.path.splitext(uploaded_file.name)[1] or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        return tmp.name


class StaffRequiredMixin:
    """Allow only staff users, redirecting everyone else to the home page."""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "Раздел управления справочниками доступен только сотрудникам библиотеки.")
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)


class ReferenceDashboardView(StaffRequiredMixin, TemplateView):
    """Staff dashboard with reference counters and upload forms."""

    template_name = "references/dashboard.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "institute_count": Institute.objects.count(),
                "department_count": Department.objects.count(),
                "specialty_count": Specialty.objects.count(),
                "program_count": Program.objects.count(),
                "education_level_count": EducationLevel.objects.count(),
                "latest_imports": ImportLog.objects.select_related("uploaded_by")[:10],
            }
        )
        return context


class UploadKugView(StaffRequiredMixin, View):
    """Handle staff КУГ xlsx uploads."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> HttpResponse:
        return _handle_upload(
            request=request,
            source=ImportLog.SOURCE_KUG,
            parser=parse_kug,
            saver=save_kug_records,
            success_message="Сводный КУГ загружен.",
        )


class UploadSrView(StaffRequiredMixin, View):
    """Handle staff штатная расстановка xlsx uploads."""

    http_method_names = ["post"]

    def post(self, request: HttpRequest) -> HttpResponse:
        return _handle_upload(
            request=request,
            source=ImportLog.SOURCE_SR,
            parser=parse_sr,
            saver=save_sr_records,
            success_message="Штатная расстановка загружена.",
        )


class ImportListView(StaffRequiredMixin, ListView):
    """Paginated staff import history."""

    model = ImportLog
    template_name = "references/import_list.html"
    context_object_name = "imports"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[ImportLog]:
        return ImportLog.objects.select_related("uploaded_by").all()


class ImportDetailView(StaffRequiredMixin, DetailView):
    """Staff import log detail page."""

    model = ImportLog
    template_name = "references/import_detail.html"
    context_object_name = "import_log"


def _handle_upload(
    *,
    request: HttpRequest,
    source: str,
    parser: Callable,
    saver: Callable,
    success_message: str,
) -> HttpResponse:
    """Shared xlsx upload, parse, save and ImportLog creation flow."""
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        messages.error(request, "Выберите файл .xlsx для загрузки.")
        return redirect("references:dashboard")

    if not uploaded_file.name.lower().endswith(".xlsx"):
        messages.error(request, "Поддерживаются только файлы .xlsx.")
        return redirect("references:dashboard")

    tmp_path = _save_uploaded_xlsx(uploaded_file)
    try:
        parsed_records, parse_errors = parser(tmp_path)
        stats = saver(parsed_records) if parsed_records else ImportStats()
    except Exception as exc:
        parse_errors = [f"Критическая ошибка импорта: {exc}"]
        stats = ImportStats()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    status = _status_for_import(stats.created, stats.skipped, len(parse_errors))
    ImportLog.objects.create(
        source=source,
        filename=uploaded_file.name,
        uploaded_by=request.user,
        created=stats.created,
        skipped=stats.skipped,
        errors=len(parse_errors),
        error_log="\n".join(parse_errors),
        status=status,
    )

    if status == "error":
        messages.error(request, "Импорт завершился с ошибкой. Записи не созданы.")
    elif status == "partial":
        messages.warning(request, f"{success_message} Есть ошибки в отдельных строках: {len(parse_errors)}.")
    else:
        messages.success(request, success_message)

    return redirect("references:dashboard")

def departments_by_institute(request):
    institute_id = request.GET.get("institute_id")
    if not institute_id:
        return JsonResponse({"results": []})

    qs = Department.objects.filter(institute_id=institute_id).order_by("name")
    return JsonResponse({
        "results": [{"id": d.id, "name": d.name} for d in qs]
    })

def specialties_by_institute_and_level(request):
    institute_id = request.GET.get("institute_id")
    level_id = request.GET.get("education_level_id")
    if not institute_id or not level_id:
        return JsonResponse({"results": []})

    qs = (Program.objects
          .filter(institute_id=institute_id, education_level_id=level_id)
          .select_related("specialty")
          .order_by("specialty__code"))

    # уникальные направления (на случай дублей)
    seen = set()
    results = []
    for p in qs:
        if p.specialty_id in seen:
            continue
        seen.add(p.specialty_id)
        results.append({
            "id": p.specialty_id,
            "label": str(p.specialty),
        })

    return JsonResponse({"results": results})
