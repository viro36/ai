import os

import pandas as pd
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.coverage_analysis.models import (
    CoverageMethodology,
    CoverageScenario,
)
from ._methodology_parser import parse_methodology_sheet

METHODOLOGY_SHEET = "Методика"

DEFAULT_DOCS_DIR = Path(__file__).resolve().parents[2] / "management" / "docs"

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


class Command(BaseCommand):
    help = (
        "Загружает только лист 'Методика' из файлов анализа покрытия. "
        "Общие разделы (1–7) сохраняются один раз, сценарные — по сценарию."
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
            self.stdout.write(f"\n=== Методика из: {file_path} ===")

            if not os.path.exists(file_path):
                self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
                continue

            scenario = self._detect_scenario(file_path)

            if scenario_filter and scenario != scenario_filter:
                self.stdout.write(
                    self.style.WARNING(
                        f"Пропускаем (сценарий {scenario} != {scenario_filter}): "
                        f"{file_path}"
                    )
                )
                continue

            try:
                xls = pd.read_excel(file_path, sheet_name=None, header=None)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Не удалось прочитать файл: {e}"))
                continue

            if METHODOLOGY_SHEET not in xls:
                self.stdout.write(
                    self.style.WARNING(
                        f"Лист '{METHODOLOGY_SHEET}' не найден, пропускаем."
                    )
                )
                continue

            with transaction.atomic():
                self._load_methodology(xls[METHODOLOGY_SHEET], scenario)

        self.stdout.write(self.style.SUCCESS("\nГотово."))

    # ---------- Вспомогательные ----------
    def _get_default_files(self, scenario_filter=None):
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
        filename = os.path.basename(file_path).lower()
        if "не по специальности" in filename or "мигрируют" in filename:
            return CoverageScenario.REALISTIC
        return CoverageScenario.OPTIMISTIC

    def _load_methodology(self, df, scenario):
        rows = parse_methodology_sheet(df, scenario)

        # Удаляем сценарные разделы этого сценария И все общие
        # (общие всё равно пересоздаются — они одинаковы для всех файлов).
        CoverageMethodology.objects.filter(
            Q(scenario=scenario) | Q(scenario__isnull=True)
        ).delete()

        general = 0
        scoped = 0
        for row in rows:
            CoverageMethodology.objects.create(**row)
            if row["scenario"] is None:
                general += 1
            else:
                scoped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Методика: общих разделов — {general}, " f"сценарных — {scoped}."
            )
        )
