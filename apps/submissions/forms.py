from django import forms
from django.core.exceptions import ValidationError

from apps.references.models import Department, Program, Specialty
from apps.validation.file_validators import validate_pdf_upload
from apps.validation.normalization import normalize_whitespace
from apps.validation.text_validators import (
    validate_author_full_name,
    validate_supervisor_full_name,
    validate_not_mostly_caps,
    validate_page_count,
    validate_title_no_quotes,
    validate_year,
)

from .models import Submission


class SubmissionCreateForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            "author_full_name",
            "supervisor_full_name",
            "work_title",
            "year",
            "page_count",
            "document_type",

            # сначала уровень, потом школа, потом направления
            "education_level",
            "institute",
            "specialty",

            # кафедра зависит от школы
            "department",

            "file",
        ]
        widgets = {
            "year": forms.NumberInput(attrs={"min": 1900, "max": 2100}),
            "page_count": forms.NumberInput(attrs={"min": 1, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # На клиенте: только 1 файл и только pdf
        self.fields["file"].widget.attrs.update({"accept": ".pdf,application/pdf"})

        # По умолчанию зависимые списки пустые
        self.fields["department"].queryset = Department.objects.none()
        self.fields["specialty"].queryset = Specialty.objects.none()

        # Достанем выбранные значения (из POST или из instance)
        level_id = None
        institute_id = None

        if "education_level" in self.data:
            level_id = self.data.get("education_level")
        elif getattr(self.instance, "education_level_id", None):
            level_id = self.instance.education_level_id

        if "institute" in self.data:
            institute_id = self.data.get("institute")
        elif getattr(self.instance, "institute_id", None):
            institute_id = self.instance.institute_id

        # Кафедры зависят только от школы
        if institute_id:
            try:
                iid = int(institute_id)
                self.fields["department"].queryset = Department.objects.filter(institute_id=iid).order_by("name")
            except (TypeError, ValueError):
                pass

        # Направления зависят от школы + уровня
        if institute_id and level_id:
            try:
                iid = int(institute_id)
                lid = int(level_id)
                sp_ids = Program.objects.filter(
                    institute_id=iid,
                    education_level_id=lid
                ).values_list("specialty_id", flat=True)
                self.fields["specialty"].queryset = Specialty.objects.filter(id__in=sp_ids).order_by("code")
            except (TypeError, ValueError):
                pass

    def clean_author_full_name(self):
        v = normalize_whitespace(self.cleaned_data.get("author_full_name", ""))
        v = validate_author_full_name(v)
        return v

    def clean_supervisor_full_name(self):
        v = normalize_whitespace(self.cleaned_data.get("supervisor_full_name", ""))
        v = validate_supervisor_full_name(v)  # у тебя уже без инициалов
        return v

    def clean_work_title(self):
        v = normalize_whitespace(self.cleaned_data.get("work_title", ""))
        validate_title_no_quotes(v)
        validate_not_mostly_caps(v, field_label="Название работы")
        return v

    def clean_year(self):
        v = self.cleaned_data.get("year")
        validate_year(v)
        return v

    def clean_page_count(self):
        v = self.cleaned_data.get("page_count")
        validate_page_count(v)
        return v

    def clean_file(self):
        f = self.cleaned_data.get("file")
        validate_pdf_upload(f)
        return f

    def clean(self):
        cleaned = super().clean()

        institute = cleaned.get("institute")
        department = cleaned.get("department")
        level = cleaned.get("education_level")
        specialty = cleaned.get("specialty")

        # кафедра принадлежит школе
        if institute and department and department.institute_id != institute.id:
            raise ValidationError("Выбранная кафедра не относится к выбранному институту.")

        # выбранное направление действительно доступно для (уровень + школа)
        if institute and level and specialty:
            ok = Program.objects.filter(
                institute=institute,
                education_level=level,
                specialty=specialty
            ).exists()
            if not ok:
                raise ValidationError("Выбранное направление недоступно для указанного института и уровня образования.")

        return cleaned