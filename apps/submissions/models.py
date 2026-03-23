import os

from django.conf import settings
from django.db import models

from apps.references.models import Department, DocumentType, EducationLevel, Institute, Specialty


def submission_upload_path(instance, filename: str) -> str:
    _, ext = os.path.splitext(filename)
    safe_ext = (ext or ".pdf").lower()
    sid = instance.id or "tmp"
    return f"vkr_files/user_{instance.user_id}/submission_{sid}/document{safe_ext}"


class SubmissionStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    SUBMITTED = "submitted", "Отправлено"
    NEEDS_FIX = "needs_fix", "Требует исправлений"
    ACCEPTED = "accepted", "Принято"


class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Пользователь",
    )

    author_full_name = models.CharField("ФИО автора", max_length=255)
    supervisor_full_name = models.CharField("ФИО руководителя", max_length=255)
    work_title = models.CharField("Название работы", max_length=500)
    year = models.PositiveIntegerField("Год")
    page_count = models.PositiveIntegerField("Количество страниц")

    institute = models.ForeignKey(Institute, on_delete=models.PROTECT, verbose_name="Институт/школа")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name="Кафедра/департамент")
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, verbose_name="Направление/специальность")
    education_level = models.ForeignKey(EducationLevel, on_delete=models.PROTECT, verbose_name="Уровень образования")
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, verbose_name="Тип документа")

    file = models.FileField("Файл (PDF)", upload_to=submission_upload_path)
    original_file_name = models.CharField("Исходное имя файла", max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField("Размер файла (байт)", default=0)
    file_extension = models.CharField("Расширение файла", max_length=16, blank=True)

    status = models.CharField(
        "Статус",
        max_length=32,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.DRAFT,
    )
    staff_comment = models.TextField("Комментарий проверяющего", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заявка #{self.id} ({self.get_status_display()})"

    @property
    def display_file_name(self) -> str:
        preferred_name = (self.original_file_name or "").strip()
        if preferred_name:
            return preferred_name

        if self.file and self.file.name:
            return os.path.basename(self.file.name)

        return "PDF-документ"

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, "name"):
            current_name = os.path.basename(self.file.name)
            if current_name and not self.original_file_name:
                self.original_file_name = current_name

        if self.file and hasattr(self.file, "size"):
            self.file_size = self.file.size
            _, ext = os.path.splitext(self.file.name)
            self.file_extension = (ext or "").lower()

        super().save(*args, **kwargs)
