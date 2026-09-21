from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
)


# ---------- Кастомные фильтры ----------
class CoverageYearFilter(admin.SimpleListFilter):
    """Фильтр по годам, построенный динамически из данных."""

    title = "Год"
    parameter_name = "year"

    def lookups(self, request, model_admin):
        years = (
            CoverageAnalysisSummary.objects.values_list("year", flat=True)
            .distinct()
            .order_by("year")
        )
        return [(y, str(y)) for y in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=self.value())
        return queryset


class CoverageYearEntryFilter(admin.SimpleListFilter):
    """Фильтр по годам для записей (могут быть года, которых нет в сводке)."""

    title = "Год"
    parameter_name = "year"

    def lookups(self, request, model_admin):
        years = (
            CoverageAnalysisEntry.objects.values_list("year", flat=True)
            .distinct()
            .order_by("year")
        )
        return [(y, str(y)) for y in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(year=self.value())
        return queryset


class DeltaSignFilter(admin.SimpleListFilter):
    """Фильтр по знаку дельты: только дефицит или только профицит."""

    title = "Знак дельты"
    parameter_name = "delta_sign"

    def lookups(self, request, model_admin):
        return (
            ("positive", "Профицит (delta > 0)"),
            ("negative", "Дефицит (delta < 0)"),
            ("zero", "Нулевая (delta = 0)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "positive":
            return queryset.filter(delta__gt=0)
        if self.value() == "negative":
            return queryset.filter(delta__lt=0)
        if self.value() == "zero":
            return queryset.filter(delta=0)
        return queryset


class CoverageRangeFilter(admin.SimpleListFilter):
    """Фильтр по уровню покрытия."""

    title = "Уровень покрытия"
    parameter_name = "coverage_range"

    def lookups(self, request, model_admin):
        return (
            ("none", "Нет покрытия (0%)"),
            ("low", "Низкое (0–50%)"),
            ("medium", "Среднее (50–80%)"),
            ("high", "Высокое (80–100%)"),
            ("over", "Перепроизводство (>100%)"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "none":
            return queryset.filter(coverage_percent=0)
        if v == "low":
            return queryset.filter(coverage_percent__gt=0, coverage_percent__lt=50)
        if v == "medium":
            return queryset.filter(coverage_percent__gte=50, coverage_percent__lt=80)
        if v == "high":
            return queryset.filter(coverage_percent__gte=80, coverage_percent__lte=100)
        if v == "over":
            return queryset.filter(coverage_percent__gt=100)
        return queryset


class NeedRangeFilter(admin.SimpleListFilter):
    """Фильтр по величине потребности."""

    title = "Потребность, чел."
    parameter_name = "need_range"

    def lookups(self, request, model_admin):
        return (
            ("lt100", "до 100"),
            ("100_500", "100–500"),
            ("500_1000", "500–1000"),
            ("gt1000", "более 1000"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "lt100":
            return queryset.filter(need__lt=100)
        if v == "100_500":
            return queryset.filter(need__gte=100, need__lt=500)
        if v == "500_1000":
            return queryset.filter(need__gte=500, need__lt=1000)
        if v == "gt1000":
            return queryset.filter(need__gte=1000)
        return queryset


# ---------- Админка сводки ----------
@admin.register(CoverageAnalysisSummary)
class CoverageAnalysisSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "scenario",
        "annual_closed_need",
        "graduate_supply",
        "overall_coverage_percent_display",
        "cat_closes",
        "cat_surplus",
        "cat_partial",
        "cat_not_closes",
        "total_groups_with_need",
    )
    list_filter = (
        "scenario",
        CoverageYearFilter,
    )
    ordering = ("scenario", "year")
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("scenario", "year")}),
        (
            "Основные показатели",
            {
                "fields": (
                    "annual_closed_need",
                    "graduate_supply",
                    "overall_coverage_percent",
                )
            },
        ),
        (
            "Число ОКЗ-групп по категориям",
            {
                "fields": (
                    "cat_closes",
                    "cat_surplus",
                    "cat_partial",
                    "cat_not_closes",
                    "cat_not_closes_no_programs",
                    "cat_sector_shrink",
                    "cat_career_growth",
                    "cat_no_prof_training",
                    "cat_no_need",
                )
            },
        ),
        ("Итого", {"fields": ("total_groups_with_need",)}),
    )

    def overall_coverage_percent_display(self, obj):
        if obj.overall_coverage_percent is None:
            return "—"
        pct = obj.overall_coverage_percent
        if pct >= 100:
            color = "green"
        elif pct >= 80:
            color = "orange"
        else:
            color = "red"
        # Сначала форматируем число в строку, потом подставляем
        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            f"{pct:.1f}%",
        )

    overall_coverage_percent_display.short_description = "Общее покрытие"
    overall_coverage_percent_display.admin_order_field = "overall_coverage_percent"


# ---------- Админка записей ----------
@admin.register(CoverageAnalysisEntry)
class CoverageAnalysisEntryAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "scenario",
        "source",
        "block",
        "position",
        "okz_code",
        "okz_name_short",
        "need",
        "supply",
        "coverage_percent_display",
        "delta_display",
    )
    list_filter = (
        "scenario",
        CoverageYearEntryFilter,
        "source",
        "block",
        DeltaSignFilter,
        CoverageRangeFilter,
        NeedRangeFilter,
    )
    search_fields = (
        "okz_code",
        "okz_name",
    )
    ordering = ("scenario", "year", "source", "block", "position")
    list_per_page = 50
    list_max_show_all = 500

    # Ускоряем выборку, чтобы не тормозило
    list_select_related = False

    fieldsets = (
        (None, {"fields": ("scenario", "year", "source", "block", "position")}),
        ("ОКЗ-группа", {"fields": ("okz_code", "okz_name")}),
        ("Показатели", {"fields": ("need", "supply", "coverage_percent", "delta")}),
    )

    def okz_name_short(self, obj):
        if not obj.okz_name:
            return "—"
        return obj.okz_name[:80] + "…" if len(obj.okz_name) > 80 else obj.okz_name

    okz_name_short.short_description = "Наименование"
    okz_name_short.admin_order_field = "okz_name"

    def coverage_percent_display(self, obj):
        if obj.coverage_percent is None:
            return "—"
        pct = obj.coverage_percent
        if pct >= 150:
            color = "#0a7d00"  # тёмно-зелёный — профицит
        elif pct >= 100:
            color = "green"
        elif pct >= 80:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            f"{pct:.1f}",
        )

    coverage_percent_display.short_description = "Покрытие, %"
    coverage_percent_display.admin_order_field = "coverage_percent"

    def delta_display(self, obj):
        if obj.delta is None:
            return "—"
        if obj.delta > 0:
            return format_html(
                '<span style="color:green;">+{}</span>',
                f"{obj.delta:.0f}",
            )
        if obj.delta < 0:
            return format_html(
                '<span style="color:red;">{}</span>',
                f"{obj.delta:.0f}",
            )
        return "0"

    delta_display.short_description = "Дефицит/Излишек"
    delta_display.admin_order_field = "delta"

    # Опционально: экшены для быстрого переключения вида
    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="coverage_entries.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Год",
                "Сценарий",
                "Источник",
                "Блок",
                "Позиция",
                "Код ОКЗ",
                "Наименование",
                "Потребность",
                "Предложение",
                "Покрытие, %",
                "Дельта",
            ]
        )
        for obj in queryset:
            writer.writerow(
                [
                    obj.year,
                    obj.get_scenario_display(),
                    obj.get_source_display(),
                    obj.get_block_display(),
                    obj.position,
                    obj.okz_code,
                    obj.okz_name,
                    obj.need,
                    obj.supply,
                    obj.coverage_percent,
                    obj.delta,
                ]
            )
        return response

    export_as_csv.short_description = "Экспортировать в CSV"
