import re
from datetime import datetime
from django.core.exceptions import ValidationError
from .normalization import normalize_whitespace

QUOTE_CHARS = {'"', "«", "»", "“", "”", "„", "‟", "'"}

# Разрешим кириллицу/латиницу + дефис (Фамилия-Имя)
NAME_PART_RE = re.compile(r"^[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*$")

def _letters_stats(s: str) -> tuple[int, int]:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return (0, 0)
    upper = sum(1 for c in letters if c.isupper())
    return (len(letters), upper)

def validate_not_mostly_caps(value: str, *, field_label: str = "Поле") -> None:
    value = normalize_whitespace(value)
    total, upper = _letters_stats(value)
    if total == 0:
        return
    # Если почти все буквы верхнего регистра — считаем капсом.
    if upper / total >= 0.7:
        raise ValidationError(f"{field_label}: не вводите текст капсом (верхним регистром).")

def validate_title_no_quotes(value: str) -> None:
    value = normalize_whitespace(value)
    if any(ch in value for ch in QUOTE_CHARS):
        raise ValidationError("Название работы должно быть без кавычек.")

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

    # проверим каждую часть
    for p in parts:
        # инициалы вида "И." или "И.А." (если разрешены)
        if allow_initials and re.fullmatch(r"[A-Za-zА-ЯЁ]\.", p):
            continue

        if not NAME_PART_RE.fullmatch(p):
            raise ValidationError("ФИО должно содержать только русские буквы и дефис.")

        # запрет одиночных букв (кроме инициалов)
        if len(p.replace("-", "")) == 1:
            raise ValidationError("ФИО не должно состоять из одиночных символов.")

        # требуем нормальный регистр: первая заглавная, остальные строчные
        # (для частей с дефисом проверим обе половины)
        for chunk in p.split("-"):
            if len(chunk) >= 2:
                if not (chunk[0].isupper() and chunk[1:].islower()):
                    raise ValidationError("ФИО должно быть записано с заглавной буквы, без капса.")

    # общий запрет “всё капсом”
    validate_not_mostly_caps(value, field_label="ФИО")
    return value

def validate_author_full_name(value: str) -> str:
    # Автор: строго “полное ФИО”, без инициалов
    return _validate_full_name(value, allow_initials=False)

def validate_supervisor_full_name(value: str) -> str:
    return _validate_full_name(value, allow_initials=False)