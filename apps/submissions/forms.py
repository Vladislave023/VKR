from django import forms
from django.core.exceptions import ValidationError

from apps.references.models import Department, Program, Specialty
from apps.validation.file_validators import validate_pdf_upload
from apps.validation.normalization import normalize_whitespace
from apps.validation.text_validators import (
    validate_author_full_name,
    validate_page_count,
    validate_supervisor_full_name,
    validate_work_title,
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
            "education_level",
            "institute",
            "specialty",
            "department",
            "file",
        ]
        widgets = {
            "work_title": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
            "year": forms.NumberInput(attrs={"min": 1900, "max": 2100}),
            "page_count": forms.NumberInput(attrs={"min": 1, "max": 5000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget
            base_class = "form-select" if isinstance(widget, forms.Select) else "form-control"
            current_classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{current_classes} {base_class}".strip()

        self.fields["work_title"].widget.attrs.update({
            "rows": 3,
            "maxlength": Submission._meta.get_field("work_title").max_length,
            "placeholder": "Укажите полное название работы",
        })
        self.fields["file"].widget.attrs.update({"accept": ".pdf,application/pdf"})
        self.fields["document_type"].queryset = self.fields["document_type"].queryset.exclude(name="ВКР").order_by("name")

        self.fields["department"].queryset = Department.objects.none()
        self.fields["specialty"].queryset = Specialty.objects.none()

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

        if institute_id:
            try:
                iid = int(institute_id)
                self.fields["department"].queryset = Department.objects.filter(institute_id=iid).order_by("name")
            except (TypeError, ValueError):
                pass

        if institute_id and level_id:
            try:
                iid = int(institute_id)
                lid = int(level_id)
                specialty_ids = Program.objects.filter(
                    institute_id=iid,
                    education_level_id=lid,
                ).values_list("specialty_id", flat=True)
                self.fields["specialty"].queryset = Specialty.objects.filter(id__in=specialty_ids).order_by("code")
            except (TypeError, ValueError):
                pass

    def clean_author_full_name(self):
        value = normalize_whitespace(self.cleaned_data.get("author_full_name", ""))
        return validate_author_full_name(value)

    def clean_supervisor_full_name(self):
        value = normalize_whitespace(self.cleaned_data.get("supervisor_full_name", ""))
        return validate_supervisor_full_name(value)

    def clean_work_title(self):
        value = normalize_whitespace(self.cleaned_data.get("work_title", ""))
        return validate_work_title(value)

    def clean_year(self):
        value = self.cleaned_data.get("year")
        validate_year(value)
        return value

    def clean_page_count(self):
        value = self.cleaned_data.get("page_count")
        validate_page_count(value)
        return value

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        validate_pdf_upload(uploaded_file)
        return uploaded_file

    def clean(self):
        cleaned = super().clean()

        institute = cleaned.get("institute")
        department = cleaned.get("department")
        level = cleaned.get("education_level")
        specialty = cleaned.get("specialty")

        if institute and department and department.institute_id != institute.id:
            raise ValidationError("Выбранная кафедра не относится к указанному институту/школе.")

        if institute and level and specialty:
            is_available = Program.objects.filter(
                institute=institute,
                education_level=level,
                specialty=specialty,
            ).exists()
            if not is_available:
                raise ValidationError(
                    "Выбранное направление недоступно для указанного института/школы и уровня образования."
                )

        return cleaned
