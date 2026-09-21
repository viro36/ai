from django.db import models


class Year(models.Model):
    """Модель для хранения годов."""

    year = models.PositiveIntegerField(unique=True, verbose_name="Год")

    def __str__(self):
        return str(self.year)

    class Meta:
        verbose_name = "Год"
        verbose_name_plural = "Годы"
        ordering = ["year"]


class NeedType(models.Model):
    """Модель для типа потребности (Общее/Замещение)."""

    name = models.CharField(max_length=50, unique=True, verbose_name="Тип потребности")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип потребности"
        verbose_name_plural = "Типы потребности"


class Occupation(models.Model):
    """Справочник начальных групп занятий."""

    code = models.CharField(
        max_length=20, unique=True, verbose_name="Код начальной группы занятий"
    )
    name = models.TextField(verbose_name="Наименование начальной группы занятий")

    def __str__(self):
        return f"{self.code} - {self.name[:50]}..."

    class Meta:
        verbose_name = "Начальная группа занятий"
        verbose_name_plural = "Начальные группы занятий"
        ordering = ["code"]


class EconomicActivity(models.Model):
    """Справочник разделов видов экономической деятельности."""

    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Раздел вида экономической деятельности",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Раздел вида экономической деятельности"
        verbose_name_plural = "Разделы видов экономической деятельности"
        ordering = ["name"]


class LaborNeed(models.Model):
    """Основная таблица для хранения значений кадровой потребности."""

    year = models.ForeignKey(Year, on_delete=models.CASCADE, verbose_name="Год")
    need_type = models.ForeignKey(
        NeedType, on_delete=models.CASCADE, verbose_name="Тип потребности"
    )
    occupation = models.ForeignKey(
        Occupation, on_delete=models.CASCADE, verbose_name="Начальная группа занятий"
    )
    economic_activity = models.ForeignKey(
        EconomicActivity,
        on_delete=models.CASCADE,
        verbose_name="Раздел вида экономической деятельности",
    )
    value = models.FloatField(verbose_name="Значение")
    source_file = models.CharField(
        max_length=255, blank=True, verbose_name="Исходный файл"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"{self.year} | {self.need_type} | {self.occupation.code} | {self.economic_activity.name[:30]}... | {self.value}"

    class Meta:
        verbose_name = "Кадровая потребность"
        verbose_name_plural = "Кадровая потребность"
        unique_together = ("year", "need_type", "occupation", "economic_activity")
        indexes = [
            models.Index(
                fields=["year", "need_type", "occupation", "economic_activity"]
            ),
        ]
