from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.references.adapters.sr_adapter import parse_sr
from apps.references.services import save_sr_records


class Command(BaseCommand):
    """Load institutes and departments from a staff allocation xlsx workbook."""

    help = "Load institutes and departments from a штатная расстановка .xlsx file."

    def add_arguments(self, parser) -> None:
        parser.add_argument("filepath", help="Path to the штатная расстановка .xlsx file")

    def handle(self, *args, **options) -> None:
        path = Path(options["filepath"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        if path.suffix.lower() != ".xlsx":
            raise CommandError("Only .xlsx files are supported.")

        school_department_map, errors = parse_sr(str(path))
        stats = save_sr_records(school_department_map)
        department_total = sum(len(items) for items in school_department_map.values())

        self.stdout.write(
            self.style.SUCCESS(
                "SR import: "
                f"schools={len(school_department_map)}, departments={department_total}, "
                f"created={stats.created}, skipped={stats.skipped}, errors={len(errors)}"
            )
        )
        for error in errors:
            self.stderr.write(error)
