from __future__ import annotations

from django.apps import apps
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.references.models import Department, Institute, Program


INSTITUTE_ALIASES: dict[str, str] = {
    "ВИ-ШРМИ": "Восточный институт",
    "Восточный институт (Школа)": "Восточный институт",
    "ИМКТ": "Институт математики и компьютерных наук",
    "Институт математики и компьютерных технологий (Школа)": "Институт математики и компьютерных наук",
    "ИМО": "Институт Мирового океана",
    "Институт Мирового океана (Школа)": "Институт Мирового океана",
    "ИНТиПМ": "Институт наукоемких технологий и передовых материалов",
    "Институт наукоемких технологий и передовых материалов (Школа)": "Институт наукоемких технологий и передовых материалов",
    "ИФКиС": "Институт физической культуры и спорта",
    "Институт физической культуры и спорта (Школа)": "Институт физической культуры и спорта",
    "ПИШ ИББПС": "Передовая инженерная школа «Институт биотехнологий, биоинженерии и пищевых систем»",
    "Политех": "Политехнический институт",
    "Политехнический институт (Школа)": "Политехнический институт",
    "ШИГН": "Школа искусств и гуманитарных наук",
    "ШМиНЖ": "Школа медицины и наук о жизни",
    "ШП": "Школа педагогики",
    "ШЭМ": "Школа экономики и менеджмента",
    "ЮШ": "Юридическая школа",
}


def canonical_institute_name(name: str) -> str:
    """Return a canonical institute name for known КУГ/ШР aliases."""
    cleaned = " ".join((name or "").split())
    return INSTITUTE_ALIASES.get(cleaned, cleaned)


def _alias_candidates(canonical_name: str, aliases: list[str] | None = None) -> list[str]:
    """Build ordered alias candidates for a canonical institute name."""
    candidates = [canonical_name]
    candidates.extend(aliases or [])
    candidates.extend(alias for alias, target in INSTITUTE_ALIASES.items() if target == canonical_name)

    unique: list[str] = []
    for candidate in candidates:
        cleaned = " ".join((candidate or "").split())
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


def merge_institutes(source: Institute, target: Institute) -> None:
    """Move Programs and Departments from source institute to target institute."""
    if source.pk == target.pk:
        return

    for program in Program.objects.filter(institute=source):
        duplicate = Program.objects.filter(
            institute=target,
            education_level=program.education_level,
            specialty=program.specialty,
        ).first()
        if duplicate:
            program.delete()
        else:
            program.institute = target
            program.save(update_fields=["institute"])

    Submission = apps.get_model("submissions", "Submission")
    for department in Department.objects.filter(institute=source):
        duplicate = Department.objects.filter(institute=target, name=department.name).first()
        if duplicate:
            Submission.objects.filter(department=department).update(department=duplicate)
            department.delete()
        else:
            department.institute = target
            department.save(update_fields=["institute"])

    Submission.objects.filter(institute=source).update(institute=target)

    try:
        source.delete()
    except ProtectedError:
        pass


def resolve_institute(name: str, aliases: list[str] | None = None) -> Institute:
    """Find, create, rename or merge an institute using known aliases."""
    canonical_name = canonical_institute_name(name)
    target = Institute.objects.filter(name=canonical_name).first()

    for candidate in _alias_candidates(canonical_name, aliases):
        institute = Institute.objects.filter(name=candidate).first()
        if not institute:
            continue
        if target and institute.pk != target.pk:
            merge_institutes(institute, target)
            continue
        if not target:
            target = institute

    if target:
        if target.name != canonical_name:
            target.name = canonical_name
            try:
                target.save(update_fields=["name"])
            except IntegrityError:
                existing = Institute.objects.get(name=canonical_name)
                merge_institutes(target, existing)
                target = existing
        return target

    return Institute.objects.create(name=canonical_name)
