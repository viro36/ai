import csv
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html

from apps.coverage_analysis.constants import get_download_files

from .models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageMethodology,
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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["data_actual_date"] = timezone.localdate().strftime("%d.%m.%Y")
        return super().changelist_view(request, extra_context=extra_context)

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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["data_actual_date"] = timezone.localdate().strftime("%d.%m.%Y")
        extra_context["download_files"] = get_download_files()
        return super().changelist_view(request, extra_context=extra_context)

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

    actions = ["export_as_csv", "export_as_xlsx"]

    def export_as_csv(self, request, queryset):
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

    def export_as_xlsx(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Анализ покрытия"

        headers = [
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
        ws.append(headers)

        # Стиль шапки
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="4472C4")
        header_align = Alignment(horizontal="center", vertical="center")
        thin = Side(border_style="thin", color="D9D9D9")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        for col_idx, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = border

        # Данные
        for obj in queryset:
            ws.append(
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

        # Автоширина колонок
        for col_idx, column_cells in enumerate(ws.columns, start=1):
            max_len = 0
            for cell in column_cells:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            # Ограничим ширину разумным максимумом
            ws.column_dimensions[get_column_letter(col_idx)].width = min(
                max_len + 2, 60
            )

        # Заморозим шапку
        ws.freeze_panes = "A2"

        # Автофильтр по шапке
        ws.auto_filter.ref = ws.dimensions

        # Ответ
        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument" ".spreadsheetml.sheet"
            )
        )
        filename = "coverage_entries.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    export_as_xlsx.short_description = "Экспортировать в XLSX"


@admin.register(CoverageMethodology)
class CoverageMethodologyAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "scenario_display",
        "section_number",
        "section_title_short",
        "text_preview",
    )
    list_filter = ("scenario",)
    search_fields = ("section_number", "section_title", "text")
    ordering = ("order", "scenario")
    list_per_page = 50
    list_max_show_all = 500

    fieldsets = (
        (None, {"fields": ("scenario", "order")}),
        (
            "Содержимое",
            {"fields": ("section_number", "section_title", "text")},
        ),
    )

    def scenario_display(self, obj):
        return obj.get_scenario_display() if obj.scenario else "Общий"

    scenario_display.short_description = "Сценарий"
    scenario_display.admin_order_field = "scenario"

    def section_title_short(self, obj):
        title = (obj.section_title or "").strip()
        if not title or title.lower() == "nan":
            return "—"
        return title[:80] + "…" if len(title) > 80 else title

    section_title_short.short_description = "Раздел"
    section_title_short.admin_order_field = "section_title"

    def text_preview(self, obj):
        text = (obj.text or "").strip()
        if not text:
            return "—"
        # Заменяем переводы строк на <br>, экранируем HTML
        safe = format_html(
            '<div style="max-width: 700px; white-space: pre-wrap; '
            'font-size: 12px; line-height: 1.4;">{}</div>',
            text,
        )
        return safe

    text_preview.short_description = "Текст"
