from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import SubmissionCreateForm, SubmissionUpdateForm
from .models import Submission, SubmissionStatus


def wants_json(request) -> bool:
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


@login_required
def submission_create_view(request):
    if request.method == "POST":
        form = SubmissionCreateForm(request.POST, request.FILES)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.user = request.user
            sub.status = SubmissionStatus.SUBMITTED
            sub.save()

            if wants_json(request):
                return JsonResponse({
                    "ok": True,
                    "redirect_url": reverse("submissions:detail", args=[sub.pk]),
                })

            messages.success(request, "Заявка отправлена.")
            return redirect("submissions:my_list")

        if wants_json(request):
            return JsonResponse({
                "ok": False,
                "errors": form.errors.get_json_data(escape_html=True),
            }, status=400)
    else:
        form = SubmissionCreateForm()

    return render(request, "submissions/submission_form.html", {
        "form": form,
        "page_title": "Подача ВКР",
        "submit_label": "Отправить",
        "file_required": True,
    })


@login_required
def submission_edit_view(request, pk: int):
    submission = get_object_or_404(
        Submission,
        pk=pk,
        user=request.user,
        status=SubmissionStatus.NEEDS_FIX,
    )

    if request.method == "POST":
        form = SubmissionUpdateForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.status = SubmissionStatus.SUBMITTED
            sub.staff_comment = ""

            uploaded_file = request.FILES.get("file")
            if uploaded_file:
                sub.original_file_name = uploaded_file.name

            sub.save()

            if wants_json(request):
                return JsonResponse({
                    "ok": True,
                    "redirect_url": reverse("submissions:detail", args=[sub.pk]),
                })

            messages.success(request, "Исправленная заявка отправлена повторно.")
            return redirect("submissions:detail", pk=sub.pk)

        if wants_json(request):
            return JsonResponse({
                "ok": False,
                "errors": form.errors.get_json_data(escape_html=True),
            }, status=400)
    else:
        form = SubmissionUpdateForm(instance=submission)

    return render(request, "submissions/submission_form.html", {
        "form": form,
        "submission": submission,
        "page_title": f"Исправление заявки #{submission.pk}",
        "submit_label": "Отправить повторно",
        "file_required": False,
    })


@login_required
def my_submissions_view(request):
    qs = Submission.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "submissions/my_submissions.html", {"submissions": qs})


@login_required
def submission_detail_view(request, pk: int):
    s = get_object_or_404(Submission, pk=pk, user=request.user)
    return render(request, "submissions/submission_detail.html", {"s": s})
