import os

from django.db import migrations, models


def fill_original_file_names(apps, schema_editor):
    Submission = apps.get_model("submissions", "Submission")

    for submission in Submission.objects.exclude(file="").filter(original_file_name=""):
        submission.original_file_name = os.path.basename(submission.file.name)
        submission.save(update_fields=["original_file_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0002_submission_staff_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="original_file_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Исходное имя файла"),
        ),
        migrations.RunPython(fill_original_file_names, migrations.RunPython.noop),
    ]
