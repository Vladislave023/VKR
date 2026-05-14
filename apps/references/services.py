from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.references.canonical import resolve_institute
from apps.references.models import Department, EducationLevel, Program, Specialty


@dataclass(frozen=True)
class ImportStats:
    """Counters collected during an idempotent reference import."""

    created: int = 0
    skipped: int = 0


@transaction.atomic
def save_kug_records(records: list[dict[str, str]]) -> ImportStats:
    """Persist parsed КУГ records and count created/skipped Program rows."""
    created = 0
    skipped = 0

    for record in records:
        institute = resolve_institute(
            record["institute_name"],
            aliases=[record.get("sheet_abbr", "")],
        )
        level, _ = EducationLevel.objects.get_or_create(name=record["education_level"])
        specialty, _ = Specialty.objects.get_or_create(
            code=record["specialty_code"],
            defaults={"name": record["specialty_name"]},
        )
        _, is_created = Program.objects.get_or_create(
            institute=institute,
            education_level=level,
            specialty=specialty,
        )
        created += int(is_created)
        skipped += int(not is_created)

    return ImportStats(created=created, skipped=skipped)


@transaction.atomic
def save_sr_records(school_department_map: dict[str, list[str]]) -> ImportStats:
    """Persist parsed staff allocation records and count created/skipped Department rows."""
    created = 0
    skipped = 0

    for school_name, departments in school_department_map.items():
        institute = resolve_institute(school_name)
        for department_name in departments:
            _, is_created = Department.objects.get_or_create(
                institute=institute,
                name=department_name,
            )
            created += int(is_created)
            skipped += int(not is_created)

    return ImportStats(created=created, skipped=skipped)
