from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .text_validators import validate_work_title


class TitleValidationTests(SimpleTestCase):
    def test_all_caps_title_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_work_title("УУУУУУУУУ")

    def test_repeated_single_letter_title_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_work_title("ФФФФФФФФ")

    def test_title_with_paired_quotes_is_allowed(self):
        self.assertEqual(
            validate_work_title('Исследование метода "слоистого анализа" в инженерных данных'),
            'Исследование метода "слоистого анализа" в инженерных данных',
        )

    def test_title_with_unpaired_quotes_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_work_title('Исследование метода "слоистого анализа в инженерных данных')

    def test_title_with_excessive_punctuation_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_work_title("Анализ методов;;; обработки сигналов")
