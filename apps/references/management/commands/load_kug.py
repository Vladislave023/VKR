from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.references.adapters.kug_adapter import parse_kug
from apps.references.services import save_kug_records


class Command(BaseCommand):
    """Load reference programs from a summary КУГ xlsx workbook."""

    help = "Load institutes, education levels, specialties and programs from a КУГ .xlsx file."

    def add_arguments(self, parser) -> None:
        parser.add_argument("filepath", help="Path to the КУГ .xlsx file")

    def handle(self, *args, **options) -> None:
        path = Path(options["filepath"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        if path.suffix.lower() != ".xlsx":
            raise CommandError("Only .xlsx files are supported.")

        records, errors = parse_kug(str(path))
        stats = save_kug_records(records)

        self.stdout.write(
            self.style.SUCCESS(
                f"KUG import: records={len(records)}, created={stats.created}, skipped={stats.skipped}, errors={len(errors)}"
            )
        )
        for error in errors:
            self.stderr.write(error)
