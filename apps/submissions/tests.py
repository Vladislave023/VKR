from django.test import SimpleTestCase

from .models import Submission


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
