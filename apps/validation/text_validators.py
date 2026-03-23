import re
from datetime import datetime

from django.core.exceptions import ValidationError

from .normalization import normalize_whitespace

NAME_PART_RE = re.compile(r"^[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*$")
TITLE_PUNCTUATION_RUN_RE = re.compile(r"[.,;:!?]{3,}")


def _letters(value: str) -> list[str]:
    return [char for char in value if char.isalpha()]


def validate_not_mostly_caps(value: str, *, field_label: str = "Поле") -> None:
    value = normalize_whitespace(value)
    letters = _letters(value)
    if not letters:
        return

    if all(char.isupper() for char in letters):
        raise ValidationError(
            f"{field_label}: не используйте написание полностью прописными буквами."
        )


def _validate_balanced_quotes(value: str) -> None:
    if value.count('"') % 2 != 0:
        raise ValidationError("Если в названии используются кавычки, они должны быть парными.")

    opened = 0
    for char in value:
        if char == "«":
            opened += 1
        elif char == "»":
            if opened == 0:
                raise ValidationError("Кавычки в названии работы должны быть оформлены корректно.")
            opened -= 1

    if opened != 0:
        raise ValidationError("Кавычки в названии работы должны быть оформлены корректно.")


def validate_work_title(value: str) -> str:
    value = normalize_whitespace(value)

    if len(value) < 5:
        raise ValidationError("Название работы указано слишком кратко.")

    if len(value) > 500:
        raise ValidationError("Название работы указано слишком длинно.")

    letters = _letters(value)
    if len(letters) < 3:
        raise ValidationError("Название работы должно содержать осмысленный текст.")

    unique_letters = {char.lower() for char in letters}
    if len(letters) >= 5 and len(unique_letters) == 1:
        raise ValidationError("Название работы должно содержать осмысленный текст, а не повторение одной буквы.")

    if TITLE_PUNCTUATION_RUN_RE.search(value):
        raise ValidationError("Не используйте более двух знаков препинания подряд в названии работы.")

    _validate_balanced_quotes(value)
    validate_not_mostly_caps(value, field_label="Название работы")
    return value


def validate_year(value: int) -> None:
    current_year = datetime.now().year
    if value < 1900 or value > current_year:
        raise ValidationError(f"Год должен быть в диапазоне 1900–{current_year}.")


def validate_page_count(value: int) -> None:
    if value <= 0 or value > 5000:
        raise ValidationError("Количество страниц должно быть положительным числом (до 5000).")


def _validate_full_name(value: str, *, allow_initials: bool) -> str:
    value = normalize_whitespace(value)

    parts = value.split(" ")
    if len(parts) < 3:
        raise ValidationError("ФИО должно содержать минимум 3 части: Фамилия Имя Отчество.")

    for part in parts:
        if allow_initials and re.fullmatch(r"[A-Za-zА-ЯЁ]\.", part):
            continue

        if not NAME_PART_RE.fullmatch(part):
            raise ValidationError("ФИО должно содержать только русские буквы и дефис.")

        if len(part.replace("-", "")) == 1:
            raise ValidationError("ФИО не должно состоять из одиночных символов.")

        for chunk in part.split("-"):
            if len(chunk) >= 2 and not (chunk[0].isupper() and chunk[1:].islower()):
                raise ValidationError("ФИО должно быть записано с заглавной буквы, без CAPS.")

    validate_not_mostly_caps(value, field_label="ФИО")
    return value


def validate_author_full_name(value: str) -> str:
    return _validate_full_name(value, allow_initials=False)


def validate_supervisor_full_name(value: str) -> str:
    return _validate_full_name(value, allow_initials=False)
