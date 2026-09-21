from django.db import models


class CoverageScenario(models.TextChoices):
    OPTIMISTIC = "OPTIMISTIC", "Оптимистичный (все по специальности)"
    REALISTIC = "REALISTIC", "Реалистичный (с миграцией и нецелевым трудоустройством)"


class CoverageSource(models.TextChoices):
    ALL = "ALL", "Все источники"
    HE = "HE", "Только ВО"
    SPO = "SPO", "Только СПО"


class CoverageBlock(models.TextChoices):
    DEFICIT = "DEFICIT", "Дефицит"
    SURPLUS = "SURPLUS", "Профицит"


class CoverageAnalysisSummary(models.Model):
    """Сводка по годам (лист 'Сводка по годам')."""

    scenario = models.CharField(
        max_length=20,
        choices=CoverageScenario.choices,
        default=CoverageScenario.OPTIMISTIC,
        verbose_name="Сценарий",
    )
    year = models.PositiveIntegerField(verbose_name="Год")

    annual_closed_need = models.FloatField(
        null=True, blank=True, verbose_name="Годовая закрываемая потребность, чел."
    )
    graduate_supply = models.FloatField(
        null=True, blank=True, verbose_name="Предложение выпускников, чел."
    )
    overall_coverage_percent = models.FloatField(
        null=True, blank=True, verbose_name="Общее покрытие, %"
    )

    cat_closes = models.IntegerField(null=True, blank=True, verbose_name="ЗАКРЫВАЕТСЯ")
    cat_surplus = models.IntegerField(null=True, blank=True, verbose_name="ПРОФИЦИТ")
    cat_partial = models.IntegerField(null=True, blank=True, verbose_name="ЧАСТИЧНО")
    cat_not_closes = models.IntegerField(
        null=True, blank=True, verbose_name="НЕ ЗАКРЫВАЕТСЯ"
    )
    cat_not_closes_no_programs = models.IntegerField(
        null=True, blank=True, verbose_name="НЕ ЗАКРЫВАЕТСЯ (нет программ)"
    )
    cat_sector_shrink = models.IntegerField(
        null=True, blank=True, verbose_name="ВЫПУСК ПРИ СЖАТИИ СЕКТОРА"
    )
    cat_career_growth = models.IntegerField(
        null=True, blank=True, verbose_name="КАРЬЕРНЫЙ РОСТ (не выпускники)"
    )
    cat_no_prof_training = models.IntegerField(
        null=True, blank=True, verbose_name="НЕ ТРЕБУЕТ ПРОФ. ПОДГОТОВКИ"
    )
    cat_no_need = models.IntegerField(
        null=True, blank=True, verbose_name="ПОТРЕБНОСТИ НЕТ"
    )

    total_groups_with_need = models.IntegerField(
        null=True, blank=True, verbose_name="Групп с потребностью > 0, всего"
    )

    class Meta:
        verbose_name = "Сводка покрытия по году"
        verbose_name_plural = "Сводки покрытия по годам"
        ordering = ["scenario", "year"]
        unique_together = ("scenario", "year")

    def __str__(self):
        return f"{self.get_scenario_display()} | {self.year}"


class CoverageAnalysisEntry(models.Model):
    """Запись по одной ОКЗ-группе (листы Топ-50)."""

    scenario = models.CharField(
        max_length=20,
        choices=CoverageScenario.choices,
        default=CoverageScenario.OPTIMISTIC,
        verbose_name="Сценарий",
    )
    year = models.PositiveIntegerField(verbose_name="Год")
    source = models.CharField(
        max_length=10,
        choices=CoverageSource.choices,
        verbose_name="Источник подготовки",
    )
    block = models.CharField(
        max_length=10, choices=CoverageBlock.choices, verbose_name="Блок"
    )

    position = models.PositiveIntegerField(default=0, verbose_name="Позиция в списке")

    okz_code = models.CharField(max_length=20, verbose_name="Код ОКЗ")
    okz_name = models.TextField(verbose_name="Наименование")

    need = models.FloatField(null=True, blank=True, verbose_name="Потребность")
    supply = models.FloatField(null=True, blank=True, verbose_name="Предложение")
    coverage_percent = models.FloatField(
        null=True, blank=True, verbose_name="Покрытие, %"
    )
    delta = models.FloatField(
        null=True, blank=True, verbose_name="Дефицит/Излишек, чел."
    )

    class Meta:
        verbose_name = "Запись анализа покрытия"
        verbose_name_plural = "Записи анализа покрытия"
        ordering = ["scenario", "year", "source", "block", "position"]
        unique_together = ("scenario", "year", "source", "block", "okz_code")
        indexes = [
            models.Index(fields=["scenario", "year", "source", "block"]),
        ]

    def __str__(self):
        return f"{self.get_scenario_display()} | {self.year} | {self.source} | {self.block} | {self.okz_code}"
