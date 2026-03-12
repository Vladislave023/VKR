from django.contrib import admin
from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "document_type",
        "year",
        "status",
        "file_extension",
        "file_size",
        "created_at",
    )
    list_filter = ("status", "year", "document_type", "education_level", "institute")
    search_fields = ("author_full_name", "supervisor_full_name", "work_title", "staff_comment")