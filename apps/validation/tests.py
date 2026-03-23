from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .text_validators import validate_not_mostly_caps


class TitleValidationTests(SimpleTestCase):
    def test_short_caps_text_is_rejected(self):
        with self.assertRaises(ValidationError):
            validate_not_mostly_caps("УУУУУУУУУ", field_label="Название работы")

    def test_normal_title_passes_validation(self):
        validate_not_mostly_caps("Исследование методов машинного обучения", field_label="Название работы")
