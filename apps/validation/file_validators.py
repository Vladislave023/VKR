import os
from django.core.exceptions import ValidationError

MAX_PDF_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

def validate_pdf_upload(file) -> None:
    if not file:
        raise ValidationError("Файл не выбран.")

    # размер
    if getattr(file, "size", 0) > MAX_PDF_SIZE_BYTES:
        raise ValidationError("Файл не должен быть больше 100 МБ.")

    # расширение
    name = getattr(file, "name", "") or ""
    _, ext = os.path.splitext(name)
    if ext.lower() != ".pdf":
        raise ValidationError("Разрешён только формат PDF (.pdf).")

    # MIME (не всегда надёжно, но как доп. проверка)
    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ("application/pdf", "application/x-pdf"):
        raise ValidationError("Файл должен быть PDF (application/pdf).")

    # сигнатура PDF: первые байты должны начинаться с %PDF-
    try:
        pos = file.tell()
    except Exception:
        pos = None

    try:
        header = file.read(5)
        if header != b"%PDF-":
            raise ValidationError("Файл не похож на настоящий PDF (проверьте формат).")
    finally:
        try:
            if pos is not None:
                file.seek(pos)
            else:
                file.seek(0)
        except Exception:
            pass