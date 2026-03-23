import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.references.models import (
    Department,
    DocumentType,
    EducationLevel,
    Institute,
    Program,
    Specialty,
)

# Если нужен импорт только указанных институтов/школ — оставьте список.
# Если нужно импортировать всё, установите ALLOWED_INSTITUTES = None.
ALLOWED_INSTITUTES = {
    "ШЭМ",
    "ШП",
    "Политех",
    "ШИГН",
    "ВИ-ШРМИ",
    "ЮШ",
    "ИНТиПМ",
    "ИМО",
    "ШМиНЖ",
    "ПИШ ИББПС",
    "ИФКиС",
    "ИМКТ",
}


class Command(BaseCommand):
    help = "Import reference data from ./data (institutes, education_levels, document_types, specialties, programs, departments)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default="data",
            help="Path to data dir relative to project root (default: data)",
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[4]
        data_dir = (base_dir / options["data_dir"]).resolve()

        self.stdout.write(f"Data dir: {data_dir}")

        self.import_education_levels(data_dir / "education_levels.csv")
        self.import_document_types(data_dir / "document_types.csv")
        self.import_institutes(data_dir / "institutes.csv")
        self.import_specialties(data_dir / "specialties.csv")
        self.import_programs(data_dir / "programs.csv")

        if (data_dir / "departments.csv").exists():
            self.import_departments(data_dir / "departments.csv")
        elif (data_dir / "departments_template.csv").exists():
            self.stdout.write(
                self.style.WARNING(
                    "departments.csv не найден, импортирую departments_template.csv (если файл заполнен)."
                )
            )
            self.import_departments(data_dir / "departments_template.csv")
        else:
            self.stdout.write(self.style.WARNING("departments.csv не найден — пропускаю импорт кафедр."))

        self.stdout.write(self.style.SUCCESS("✅ Импорт завершён."))

    def _open_csv(self, path: Path):
        return path.open("r", encoding="utf-8-sig", newline="")

    def import_education_levels(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                _, is_created = EducationLevel.objects.get_or_create(name=name)
                created += int(is_created)

        self.stdout.write(f"EducationLevel: +{created} (файл {path.name})")

    def import_document_types(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                _, is_created = DocumentType.objects.get_or_create(name=name)
                created += int(is_created)

        self.stdout.write(f"DocumentType: +{created} (файл {path.name})")

    def import_institutes(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        skipped = 0
        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                name = (row.get("name") or "").strip()
                if not name:
                    continue

                if ALLOWED_INSTITUTES is not None and name not in ALLOWED_INSTITUTES:
                    skipped += 1
                    continue

                _, is_created = Institute.objects.get_or_create(name=name)
                created += int(is_created)

        self.stdout.write(f"Institute: +{created}, skipped={skipped} (файл {path.name})")

    def import_specialties(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        updated = 0
        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                code = (row.get("code") or "").strip()
                name = (row.get("name") or "").strip()
                if not code or not name:
                    continue

                _, is_created = Specialty.objects.update_or_create(
                    code=code,
                    defaults={"name": name},
                )
                created += int(is_created)
                updated += int(not is_created)

        self.stdout.write(f"Specialty: +{created}, updated={updated} (файл {path.name})")

    def import_programs(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        institutes = {item.name: item for item in Institute.objects.all()}
        levels = {item.name: item for item in EducationLevel.objects.all()}
        specialties = {item.code: item for item in Specialty.objects.all()}

        created = 0
        skipped = 0
        missing = 0

        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                institute_name = (row.get("institute") or "").strip()
                level_name = (row.get("education_level") or "").strip()
                specialty_code = (row.get("specialty_code") or "").strip()

                if not institute_name or not level_name or not specialty_code:
                    continue

                if ALLOWED_INSTITUTES is not None and institute_name not in ALLOWED_INSTITUTES:
                    skipped += 1
                    continue

                institute = institutes.get(institute_name)
                level = levels.get(level_name)
                specialty = specialties.get(specialty_code)

                if not institute or not level or not specialty:
                    missing += 1
                    continue

                _, is_created = Program.objects.get_or_create(
                    institute=institute,
                    education_level=level,
                    specialty=specialty,
                )
                created += int(is_created)

        self.stdout.write(
            f"Program: +{created}, skipped={skipped}, missing_refs={missing} (файл {path.name})"
        )

    def import_departments(self, path: Path):
        if not path.exists():
            return

        institutes = {item.name: item for item in Institute.objects.all()}

        created = 0
        skipped = 0
        missing = 0

        with self._open_csv(path) as file_obj:
            for row in csv.DictReader(file_obj):
                institute_name = (row.get("institute") or "").strip()
                department_name = (row.get("department") or "").strip()
                if not institute_name or not department_name:
                    continue

                if ALLOWED_INSTITUTES is not None and institute_name not in ALLOWED_INSTITUTES:
                    skipped += 1
                    continue

                institute = institutes.get(institute_name)
                if not institute:
                    missing += 1
                    continue

                _, is_created = Department.objects.get_or_create(
                    institute=institute,
                    name=department_name,
                )
                created += int(is_created)

        self.stdout.write(
            f"Department: +{created}, skipped={skipped}, missing_institutes={missing} (файл {path.name})"
        )
