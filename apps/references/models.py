from django.db import models


class Institute(models.Model):
    name = models.CharField("Институт/школа", max_length=255, unique=True)

    class Meta:
        verbose_name = "Институт/школа"
        verbose_name_plural = "Институты/школы"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    institute = models.ForeignKey(
        Institute,
        on_delete=models.PROTECT,
        related_name="departments",
        verbose_name="Институт/школа",
    )
    name = models.CharField("Кафедра/департамент", max_length=255)

    class Meta:
        verbose_name = "Кафедра/департамент"
        verbose_name_plural = "Кафедры/департаменты"
        ordering = ["institute__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["institute", "name"],
                name="uniq_department_per_institute",
            )
        ]

    def __str__(self):
        return f"{self.institute} — {self.name}"


class EducationLevel(models.Model):
    name = models.CharField("Уровень образования", max_length=120, unique=True)

    class Meta:
        verbose_name = "Уровень образования"
        verbose_name_plural = "Уровни образования"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    name = models.CharField("Тип документа", max_length=120, unique=True)

    class Meta:
        verbose_name = "Тип документа"
        verbose_name_plural = "Типы документов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Specialty(models.Model):
    code = models.CharField("Код направления/специальности", max_length=32, unique=True)
    name = models.CharField("Название направления/специальности", max_length=255)

    class Meta:
        verbose_name = "Направление/специальность"
        verbose_name_plural = "Направления/специальности"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"
class Program(models.Model):
    institute = models.ForeignKey(
        Institute,
        on_delete=models.PROTECT,
        verbose_name="Институт/школа",
        related_name="programs",
    )
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.PROTECT,
        verbose_name="Уровень образования",
        related_name="programs",
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        verbose_name="Направление/специальность",
        related_name="programs",
    )

    class Meta:
        verbose_name = "Программа (доступность направления)"
        verbose_name_plural = "Программы (доступность направлений)"
        constraints = [
            models.UniqueConstraint(
                fields=["institute", "education_level", "specialty"],
                name="uniq_program",
            )
        ]

    def __str__(self):
        return f"{self.education_level} | {self.institute} | {self.specialty}"