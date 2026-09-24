from django.db import models
from django.db.models import UniqueConstraint


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


class CoverageMethodology(models.Model):
    """
    Раздел методики расчёта (лист 'Методика').

    Если `scenario` пусто — раздел общий для всех сценариев
    (например, 'Закрываемая потребность', 'Выпуск ВО', 'Категории покрытия').
    Если заполнено — раздел специфичен для сценария
    (например, 'Шапка методики', 'Справочно').
    """

    scenario = models.CharField(
        max_length=20,
        choices=CoverageScenario.choices,
        blank=True,
        null=True,
        verbose_name="Сценарий",
        help_text="Пусто для общих разделов",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    section_number = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Номер",
        help_text="Например: 1, 2, 3",
    )
    section_title = models.CharField(
        max_length=255, blank=True, verbose_name="Заголовок раздела"
    )
    text = models.TextField(blank=True, verbose_name="Текст")

    class Meta:
        verbose_name = "Раздел методики"
        verbose_name_plural = "Методика расчёта"
        ordering = ["order", "scenario"]
        constraints = [
            UniqueConstraint(
                fields=["scenario", "order"],
                name="unique_methodology_scenario_order",
                nulls_distinct=False,
            ),
        ]
        indexes = [models.Index(fields=["order"])]

    def __str__(self):
        prefix = self.get_scenario_display() if self.scenario else "Общий"
        num = f"{self.section_number}. " if self.section_number else ""
        title = self.section_title[:50] if self.section_title else "—"
        return f"{prefix} | #{self.order} | {num}{title}"
