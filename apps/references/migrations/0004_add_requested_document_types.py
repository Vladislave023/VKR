from django.db import migrations


DOCUMENT_TYPES = [
    "Выпускная бакалаврская работа",
    "Научный доклад",
]


def add_document_types(apps, schema_editor):
    DocumentType = apps.get_model("references", "DocumentType")
    for name in DOCUMENT_TYPES:
        DocumentType.objects.get_or_create(name=name)


def remove_document_types(apps, schema_editor):
    DocumentType = apps.get_model("references", "DocumentType")
    DocumentType.objects.filter(name__in=DOCUMENT_TYPES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("references", "0003_importlog"),
    ]

    operations = [
        migrations.RunPython(add_document_types, remove_document_types),
    ]
