import re
import os
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.coverage_analysis.models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageSource,
    CoverageBlock,
    CoverageScenario,
)

SUMMARY_SHEET = "Сводка по годам"

TOP_SHEET_RE = re.compile(r"^Топ-50\s+(\d{4})$")
TOP_HE_SHEET_RE = re.compile(r"^Топ-50\s+только\s+ВО\s+(\d{4})$")
TOP_SPO_SHEET_RE = re.compile(r"^Топ-50\s+только\s+СПО\s+(\d{4})$")

# Папка с файлами по умолчанию: apps/coverage_analysis/management/docs/
DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "management" / "docs"

# Имена файлов по умолчанию для каждого сценария
DEFAULT_FILES = {
    CoverageScenario.OPTIMISTIC: (
        "Анализ покрытия потребности кадрами "
        "(все по выпускники устраиваются по специальности).xlsx"
    ),
    CoverageScenario.REALISTIC: (
        "Анализ покрытия потребности кадрами"
        "(доля выпускников устраивается не по специальности или мигрируют).xlsx"
    ),
}


def _to_float(value):
    if pd.isna(value):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except (ValueError, TypeError):
        return None


def _to_int(value):
    if pd.isna(value):
        return None
    try:
        return int(float(str(value).replace(",", ".").strip()))
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = (
        "Загружает файлы анализа покрытия потребности кадрами в БД. "
        "Если пути не указаны — берёт файлы из management/docs/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "file_paths",
            nargs="*",
            type=str,
            help=(
                "Пути к Excel-файлам. Если не указаны — используются файлы "
                "по умолчанию из management/docs/."
            ),
        )
        parser.add_argument(
            "--scenario",
            type=str,
            choices=[CoverageScenario.OPTIMISTIC, CoverageScenario.REALISTIC],
            help="Загрузить только один сценарий (по умолчанию — оба).",
        )

    def handle(self, *args, **options):
        file_paths = options["file_paths"]
        scenario_filter = options.get("scenario")

        # Если пути не переданы — берём файлы по умолчанию
        if not file_paths:
            file_paths = self._get_default_files(scenario_filter)
            if not file_paths:
                self.stderr.write(
                    self.style.ERROR(
                        "Не переданы пути к файлам и не найдены файлы "
                        "по умолчанию в management/docs/."
                    )
                )
                return

        for file_path in file_paths:
            self.stdout.write(f"\n=== Обработка файла: {file_path} ===")

            if not os.path.exists(file_path):
                self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
                continue

            scenario = self._detect_scenario(file_path)
            self.stdout.write(f"Сценарий: {scenario}")

            try:
                xls = pd.read_excel(file_path, sheet_name=None, header=None)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Не удалось прочитать файл: {e}"))
                continue

            with transaction.atomic():
                self._load_summary(xls, scenario)
                self._load_top_sheets(xls, scenario)

        self.stdout.write(self.style.SUCCESS("\nГотово."))

    # ---------- Вспомогательные методы ----------
    def _get_default_files(self, scenario_filter=None):
        """Возвращает список путей к файлам по умолчанию."""
        result = []
        for scenario, filename in DEFAULT_FILES.items():
            if scenario_filter and scenario != scenario_filter:
                continue
            path = DEFAULT_DOCS_DIR / filename
            if path.exists():
                result.append(str(path))
            else:
                self.stderr.write(
                    self.style.WARNING(f"Файл по умолчанию не найден: {path}")
                )
        return result

    def _detect_scenario(self, file_path):
        """Определяет сценарий по имени файла."""
        filename = os.path.basename(file_path).lower()
        if "не по специальности" in filename or "мигрируют" in filename:
            return CoverageScenario.REALISTIC
        return CoverageScenario.OPTIMISTIC

    # ---------- Сводка ----------
    def _load_summary(self, xls, scenario):
        if SUMMARY_SHEET not in xls:
            self.stdout.write(
                self.style.WARNING(f"Лист '{SUMMARY_SHEET}' не найден, пропускаем.")
            )
            return

        df = xls[SUMMARY_SHEET]

        header_row = df.iloc[0].tolist()
        year_cols = {}
        for idx, val in enumerate(header_row):
            if idx == 0:
                continue
            y = _to_int(val)
            if y:
                year_cols[y] = idx

        summary_rows = {
            "Годовая закрываемая потребность, чел.": "annual_closed_need",
            "Предложение выпускников (в пересчёте на ОКЗ), чел.": "graduate_supply",
            "Общее покрытие, %": "overall_coverage_percent",
            "ЗАКРЫВАЕТСЯ": "cat_closes",
            "ПРОФИЦИТ": "cat_surplus",
            "ЧАСТИЧНО": "cat_partial",
            "НЕ ЗАКРЫВАЕТСЯ": "cat_not_closes",
            "НЕ ЗАКРЫВАЕТСЯ (нет программ)": "cat_not_closes_no_programs",
            "ВЫПУСК ПРИ СЖАТИИ СЕКТОРА": "cat_sector_shrink",
            "КАРЬЕРНЫЙ РОСТ (не выпускники)": "cat_career_growth",
            "НЕ ТРЕБУЕТ ПРОФ. ПОДГОТОВКИ": "cat_no_prof_training",
            "ПОТРЕБНОСТИ НЕТ": "cat_no_need",
            "Групп с потребностью > 0, всего": "total_groups_with_need",
        }

        per_year = {y: {} for y in year_cols.keys()}
        for _, row in df.iloc[1:].iterrows():
            label = str(row[0]).strip()
            if label not in summary_rows:
                continue
            field = summary_rows[label]
            for y, col_idx in year_cols.items():
                value = row[col_idx]
                if field in (
                    "annual_closed_need",
                    "graduate_supply",
                    "overall_coverage_percent",
                ):
                    per_year[y][field] = _to_float(value)
                else:
                    per_year[y][field] = _to_int(value)

        for y, data in per_year.items():
            data["scenario"] = scenario
            CoverageAnalysisSummary.objects.update_or_create(
                scenario=scenario, year=y, defaults=data
            )
            self.stdout.write(self.style.SUCCESS(f"  Сводка за {y} загружена."))

    # ---------- Топ-50 ----------
    def _load_top_sheets(self, xls, scenario):
        for sheet_name, df in xls.items():
            sheet_name_clean = sheet_name.strip()

            source = None
            year = None

            m = TOP_HE_SHEET_RE.match(sheet_name_clean)
            if m:
                source = CoverageSource.HE
                year = int(m.group(1))
            else:
                m = TOP_SPO_SHEET_RE.match(sheet_name_clean)
                if m:
                    source = CoverageSource.SPO
                    year = int(m.group(1))
                else:
                    m = TOP_SHEET_RE.match(sheet_name_clean)
                    if m:
                        source = CoverageSource.ALL
                        year = int(m.group(1))

            if source is None or year is None:
                continue

            self._parse_top_sheet(df, year, source, scenario, sheet_name_clean)

    def _parse_top_sheet(self, df, year, source, scenario, sheet_name):
        values = df.values.tolist()
        n = len(values)

        blocks = []
        for i, row in enumerate(values):
            first = str(row[0]).strip() if row and row[0] is not None else ""
            if first.startswith("ТОП-50 ДЕФИЦИТНЫХ ГРУПП"):
                blocks.append((i, CoverageBlock.DEFICIT))
            elif first.startswith("ТОП-50 ПРОФИЦИТНЫХ ГРУПП"):
                blocks.append((i, CoverageBlock.SURPLUS))

        for block_idx, (start_row, block_type) in enumerate(blocks):
            data_start = start_row + 2
            if block_idx + 1 < len(blocks):
                data_end = blocks[block_idx + 1][0]
            else:
                data_end = n

            # Удаляем старые записи для этого сценария/года/источника/блока
            CoverageAnalysisEntry.objects.filter(
                scenario=scenario,
                year=year,
                source=source,
                block=block_type,
            ).delete()

            position = 0
            for i in range(data_start, data_end):
                row = values[i]
                if not row or row[0] is None:
                    continue

                okz_code = str(row[0]).strip()
                if not okz_code or okz_code.lower() == "nan":
                    continue

                okz_name = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                need = _to_float(row[2]) if len(row) > 2 else None
                supply = _to_float(row[3]) if len(row) > 3 else None
                coverage = _to_float(row[4]) if len(row) > 4 else None
                delta = _to_float(row[5]) if len(row) > 5 else None

                # Приводим дельту к знаковому виду:
                # дефицит — отрицательное, профицит — положительное
                if delta is not None:
                    if block_type == CoverageBlock.DEFICIT:
                        delta = -abs(delta)
                    elif block_type == CoverageBlock.SURPLUS:
                        delta = abs(delta)

                position += 1
                CoverageAnalysisEntry.objects.create(
                    scenario=scenario,
                    year=year,
                    source=source,
                    block=block_type,
                    position=position,
                    okz_code=okz_code,
                    okz_name=okz_name,
                    need=need,
                    supply=supply,
                    coverage_percent=coverage,
                    delta=delta,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  {sheet_name}: {block_type.label} — {position} записей."
                )
            )
