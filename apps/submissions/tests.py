import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.references.models import Department, DocumentType, EducationLevel, Institute, Program, Specialty

from .models import Submission, SubmissionStatus


class SubmissionModelTests(SimpleTestCase):
    def test_display_file_name_prefers_original_file_name(self):
        submission = Submission(
            original_file_name="Сборник РНПК 2025.pdf",
            file="vkr_files/user_1/submission_1/document.pdf",
        )
        self.assertEqual(submission.display_file_name, "Сборник РНПК 2025.pdf")

    def test_display_file_name_falls_back_to_stored_file_basename(self):
        submission = Submission(file="vkr_files/user_1/submission_1/document_abc123.pdf")
        self.assertEqual(submission.display_file_name, "document_abc123.pdf")


class SubmissionEditTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_root = tempfile.mkdtemp()
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.settings_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.settings_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="author", password="pass12345")
        self.client.force_login(self.user)

        self.institute = Institute.objects.create(name="ИМКТ")
        self.department = Department.objects.create(institute=self.institute, name="ДПИиИИ")
        self.level = EducationLevel.objects.create(name="Бакалавриат")
        self.document_type = DocumentType.objects.create(name="Выпускная бакалаврская работа")
        self.specialty = Specialty.objects.create(code="09.03.04", name="Программная инженерия")
        Program.objects.create(
            institute=self.institute,
            education_level=self.level,
            specialty=self.specialty,
        )

    def create_submission(self, *, status=SubmissionStatus.NEEDS_FIX):
        return Submission.objects.create(
            user=self.user,
            author_full_name="Иванов Иван Иванович",
            supervisor_full_name="Петров Петр Петрович",
            work_title="Разработка подсистемы валидации входных данных",
            year=2026,
            page_count=80,
            institute=self.institute,
            department=self.department,
            specialty=self.specialty,
            education_level=self.level,
            document_type=self.document_type,
            file=SimpleUploadedFile("old.pdf", b"%PDF-1.4\n%test\n", content_type="application/pdf"),
            original_file_name="old.pdf",
            status=status,
            staff_comment="Исправьте название работы.",
        )

    def form_data(self, submission):
        return {
            "author_full_name": submission.author_full_name,
            "supervisor_full_name": submission.supervisor_full_name,
            "work_title": "Разработка веб-подсистемы валидации входных данных",
            "year": submission.year,
            "page_count": submission.page_count,
            "document_type": self.document_type.id,
            "education_level": self.level.id,
            "institute": self.institute.id,
            "specialty": self.specialty.id,
            "department": self.department.id,
        }

    def test_needs_fix_submission_can_be_edited_without_new_file(self):
        submission = self.create_submission()

        response = self.client.post(
            reverse("submissions:edit", args=[submission.pk]),
            self.form_data(submission),
        )

        self.assertRedirects(response, reverse("submissions:detail", args=[submission.pk]))
        self.assertEqual(Submission.objects.count(), 1)

        submission.refresh_from_db()
        self.assertEqual(submission.status, SubmissionStatus.SUBMITTED)
        self.assertEqual(submission.staff_comment, "")
        self.assertEqual(submission.work_title, "Разработка веб-подсистемы валидации входных данных")
        self.assertEqual(submission.original_file_name, "old.pdf")

    def test_submitted_submission_cannot_be_edited_by_user(self):
        submission = self.create_submission(status=SubmissionStatus.SUBMITTED)

        response = self.client.get(reverse("submissions:edit", args=[submission.pk]))

        self.assertEqual(response.status_code, 404)
