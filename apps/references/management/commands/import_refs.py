import csv
from pathlib import Path
from django.core.management.base import BaseCommand

from apps.references.models import (
    Institute,
    Department,
    EducationLevel,
    Specialty,
    Program,
)

# Если хочешь импортировать ТОЛЬКО эти школы — оставь список.
# Если нужно импортировать всё, просто сделай ALLOWED_INSTITUTES = None
ALLOWED_INSTITUTES = {
    "ШЭМ", "ШП", "Политех", "ШИГН", "ВИ-ШРМИ", "ЮШ",
    "ИНТиПМ", "ИМО", "ШМиНЖ", "ПИШ ИББПС", "ИФКиС", "ИМКТ"
}


class Command(BaseCommand):
    help = "Import reference data from ./data (institutes, education_levels, specialties, programs, departments)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default="data",
            help="Path to data dir relative to project root (default: data)",
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[4]  # корень проекта (где manage.py)
        data_dir = (base_dir / options["data_dir"]).resolve()

        self.stdout.write(f"Data dir: {data_dir}")

        self.import_education_levels(data_dir / "education_levels.csv")
        self.import_institutes(data_dir / "institutes.csv")
        self.import_specialties(data_dir / "specialties.csv")
        self.import_programs(data_dir / "programs.csv")

        # кафедры: если есть departments.csv — импортируем, иначе попробуем departments_template.csv, иначе пропустим
        if (data_dir / "departments.csv").exists():
            self.import_departments(data_dir / "departments.csv")
        elif (data_dir / "departments_template.csv").exists():
            self.stdout.write(self.style.WARNING("departments.csv не найден, импортирую departments_template.csv (если он заполнен)."))
            self.import_departments(data_dir / "departments_template.csv")
        else:
            self.stdout.write(self.style.WARNING("departments.csv не найден — пропускаю импорт кафедр."))

        self.stdout.write(self.style.SUCCESS("✅ Импорт завершён."))

    def _open_csv(self, path: Path):
        # utf-8-sig важен для CSV из Excel (убирает BOM)
        return path.open("r", encoding="utf-8-sig", newline="")

    def import_education_levels(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        with self._open_csv(path) as f:
            for row in csv.DictReader(f):
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                _, is_created = EducationLevel.objects.get_or_create(name=name)
                created += int(is_created)

        self.stdout.write(f"EducationLevel: +{created} (файл {path.name})")

    def import_institutes(self, path: Path):
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        created = 0
        skipped = 0
        with self._open_csv(path) as f:
            for row in csv.DictReader(f):
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
        with self._open_csv(path) as f:
            for row in csv.DictReader(f):
                code = (row.get("code") or "").strip()
                name = (row.get("name") or "").strip()
                if not code or not name:
                    continue

                obj, is_created = Specialty.objects.update_or_create(
                    code=code,
                    defaults={"name": name},
                )
                created += int(is_created)
                updated += int(not is_created)

        self.stdout.write(f"Specialty: +{created}, updated={updated} (файл {path.name})")

    def import_programs(self, path: Path):
        """
        programs.csv:
        institute,education_level,specialty_code
        ИМКТ,Бакалавриат,09.03.04
        """
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Нет файла: {path.name} — пропускаю"))
            return

        # Кешируем справочники, чтобы было быстрее
        institutes = {i.name: i for i in Institute.objects.all()}
        levels = {l.name: l for l in EducationLevel.objects.all()}
        specs = {s.code: s for s in Specialty.objects.all()}

        created = 0
        skipped = 0
        missing = 0

        with self._open_csv(path) as f:
            for row in csv.DictReader(f):
                inst_name = (row.get("institute") or "").strip()
                lvl_name = (row.get("education_level") or "").strip()
                sp_code = (row.get("specialty_code") or "").strip()

                if not inst_name or not lvl_name or not sp_code:
                    continue

                if ALLOWED_INSTITUTES is not None and inst_name not in ALLOWED_INSTITUTES:
                    skipped += 1
                    continue

                inst = institutes.get(inst_name)
                lvl = levels.get(lvl_name)
                sp = specs.get(sp_code)

                if not inst or not lvl or not sp:
                    missing += 1
                    continue

                _, is_created = Program.objects.get_or_create(
                    institute=inst,
                    education_level=lvl,
                    specialty=sp,
                )
                created += int(is_created)

        self.stdout.write(f"Program: +{created}, skipped={skipped}, missing_refs={missing} (файл {path.name})")

    def import_departments(self, path: Path):
        """
        departments.csv:
        institute,department
        ИМКТ,Кафедра ...
        """
        if not path.exists():
            return

        institutes = {i.name: i for i in Institute.objects.all()}

        created = 0
        skipped = 0
        missing = 0

        with self._open_csv(path) as f:
            for row in csv.DictReader(f):
                inst_name = (row.get("institute") or "").strip()
                dep_name = (row.get("department") or "").strip()
                if not inst_name or not dep_name:
                    continue

                if ALLOWED_INSTITUTES is not None and inst_name not in ALLOWED_INSTITUTES:
                    skipped += 1
                    continue

                inst = institutes.get(inst_name)
                if not inst:
                    missing += 1
                    continue

                _, is_created = Department.objects.get_or_create(
                    institute=inst,
                    name=dep_name,
                )
                created += int(is_created)

        self.stdout.write(f"Department: +{created}, skipped={skipped}, missing_institutes={missing} (файл {path.name})")