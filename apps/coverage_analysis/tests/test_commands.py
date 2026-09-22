import pytest
from openpyxl import Workbook

from apps.coverage_analysis.models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageScenario,
    CoverageSource,
    CoverageBlock,
)

pytestmark = pytest.mark.django_db


# ---------- Хелперы для генерации Excel ----------
def _make_summary_sheet(wb, years=(2026, 2027)):
    """Лист 'Сводка по годам' с минимальным набором строк."""
    ws = wb.create_sheet("Сводка по годам")

    # Заголовок: Показатель | 2026 | 2027 | ...
    ws.append(["Показатель", *years])

    ws.append(["Годовая закрываемая потребность, чел.", *[10000 + y for y in years]])
    ws.append(
        [
            "Предложение выпускников (в пересчёте на ОКЗ), чел.",
            *[20000 + y for y in years],
        ]
    )
    ws.append(["Общее покрытие, %", *[150.0, 120.0][: len(years)]])
    ws.append(["ЗАКРЫВАЕТСЯ", *[10] * len(years)])
    ws.append(["ПРОФИЦИТ", *[5] * len(years)])
    ws.append(["ЧАСТИЧНО", *[3] * len(years)])
    ws.append(["НЕ ЗАКРЫВАЕТСЯ", *[20] * len(years)])
    ws.append(["НЕ ЗАКРЫВАЕТСЯ (нет программ)", *[15] * len(years)])
    ws.append(["ВЫПУСК ПРИ СЖАТИИ СЕКТОРА", *[2] * len(years)])
    ws.append(["КАРЬЕРНЫЙ РОСТ (не выпускники)", *[1] * len(years)])
    ws.append(["НЕ ТРЕБУЕТ ПРОФ. ПОДГОТОВКИ", *[4] * len(years)])
    ws.append(["ПОТРЕБНОСТИ НЕТ", *[6] * len(years)])
    ws.append(["Групп с потребностью > 0, всего", *[255] * len(years)])


def _make_top_sheet(wb, sheet_name, year, source_label):
    """Лист 'Топ-50 ...' с одним дефицитом и одним профицитом."""
    ws = wb.create_sheet(sheet_name)

    # Заголовок дефицита (строка 1)
    ws.append(
        [f"ТОП-50 ДЕФИЦИТНЫХ ГРУПП ({year}, {source_label}) — всего 1, показано 1"]
    )
    # Шапка таблицы (строка 2)
    ws.append(
        [
            "Код ОКЗ",
            "Наименование",
            "Потребность",
            "Предложение",
            "Покрытие, %",
            "Дефицит, чел.",
        ]
    )
    # Данные (строка 3)
    ws.append(["7511", "Обработчики", 3427, 96, 2.8, 3331])
    # Пустая строка (4)
    ws.append([])
    # Пустая строка (5)
    ws.append([])
    # Заголовок профицита (строка 6)
    ws.append(
        [f"ТОП-50 ПРОФИЦИТНЫХ ГРУПП ({year}, {source_label}) — всего 1, показано 1"]
    )
    # Шапка таблицы (строка 7)
    ws.append(
        [
            "Код ОКЗ",
            "Наименование",
            "Потребность",
            "Предложение",
            "Покрытие, %",
            "Излишек, чел.",
        ]
    )
    # Данные (строка 8)
    ws.append(["2514", "Программисты приложений", 73, 867, 1194.3, 795])


def _make_xlsx(tmp_path, filename, *, years=(2026,), sources=("ALL",)):
    """
    Создаёт xlsx с листами:
      - Сводка по годам
      - Топ-50 {year} (source=ALL)
      - Топ-50 только ВО {year} (source=HE)
      - Топ-50 только СПО {year} (source=SPO)
    По умолчанию — только ALL.
    """
    wb = Workbook()
    # Удаляем дефолтный лист
    wb.remove(wb.active)

    _make_summary_sheet(wb, years=years)

    for year in years:
        if "ALL" in sources:
            _make_top_sheet(wb, f"Топ-50 {year}", year, "все источники")
        if "HE" in sources:
            _make_top_sheet(wb, f"Топ-50 только ВО {year}", year, "только ВО")
        if "SPO" in sources:
            _make_top_sheet(wb, f"Топ-50 только СПО {year}", year, "только СПО")

    path = tmp_path / filename
    wb.save(path)
    return str(path)


# ---------- Тесты ----------
class TestLoadCoverageAnalysis:

    def test_load_optimistic_file(self, tmp_path):
        from django.core.management import call_command

        path = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026,),
            sources=("ALL", "HE", "SPO"),
        )
        call_command("load_coverage_analysis", path)

        # Сводка
        s = CoverageAnalysisSummary.objects.get(year=2026)
        assert s.scenario == CoverageScenario.OPTIMISTIC
        assert s.annual_closed_need == 12026.0
        assert s.graduate_supply == 22026.0
        assert s.total_groups_with_need == 255

        # Записи: три источника (ALL, HE, SPO), по 2 блока в каждом = 6 записей
        assert CoverageAnalysisEntry.objects.count() == 6

        # Дефицит со знаком минус
        d = CoverageAnalysisEntry.objects.get(
            source=CoverageSource.ALL, block=CoverageBlock.DEFICIT
        )
        assert d.okz_code == "7511"
        assert d.need == 3427
        assert d.delta == -3331

        # Профицит со знаком плюс
        p = CoverageAnalysisEntry.objects.get(
            source=CoverageSource.ALL, block=CoverageBlock.SURPLUS
        )
        assert p.okz_code == "2514"
        assert p.delta == 795

    def test_load_realistic_scenario_detected(self, tmp_path):
        from django.core.management import call_command

        path = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            years=(2026,),
            sources=("ALL",),
        )
        call_command("load_coverage_analysis", path)

        s = CoverageAnalysisSummary.objects.get(year=2026)
        assert s.scenario == CoverageScenario.REALISTIC

    def test_reload_does_not_duplicate(self, tmp_path):
        from django.core.management import call_command

        path = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026,),
            sources=("ALL",),
        )

        call_command("load_coverage_analysis", path)
        first_count = CoverageAnalysisEntry.objects.count()
        first_summary_count = CoverageAnalysisSummary.objects.count()

        call_command("load_coverage_analysis", path)

        assert CoverageAnalysisEntry.objects.count() == first_count
        assert CoverageAnalysisSummary.objects.count() == first_summary_count

    def test_scenario_filter(self, tmp_path):
        """--scenario OPTIMISTIC загружает только оптимистичный файл."""
        from django.core.management import call_command

        opt = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026,),
            sources=("ALL",),
        )
        real = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            years=(2026,),
            sources=("ALL",),
        )

        call_command(
            "load_coverage_analysis",
            opt,
            real,
            scenario="OPTIMISTIC",
        )

        # Загрузился только оптимистичный сценарий
        assert CoverageAnalysisSummary.objects.count() == 1
        assert (
            CoverageAnalysisSummary.objects.first().scenario
            == CoverageScenario.OPTIMISTIC
        )
        # Записи тоже только для оптимистичного
        assert set(
            CoverageAnalysisEntry.objects.values_list("scenario", flat=True)
        ) == {CoverageScenario.OPTIMISTIC}

    def test_two_scenarios_same_year(self, tmp_path):
        """Загрузка обоих файлов: две сводки за один год, разные сценарии."""
        from django.core.management import call_command

        opt = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026,),
            sources=("ALL",),
        )
        real = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            years=(2026,),
            sources=("ALL",),
        )

        call_command("load_coverage_analysis", opt, real)

        assert CoverageAnalysisSummary.objects.count() == 2
        assert set(
            CoverageAnalysisSummary.objects.values_list("scenario", flat=True)
        ) == {
            CoverageScenario.OPTIMISTIC,
            CoverageScenario.REALISTIC,
        }

    def test_source_detection_from_sheet_name(self, tmp_path):
        """Листы 'Топ-50 только ВО/СПО' → source=HE/SPO."""
        from django.core.management import call_command

        path = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026,),
            sources=("ALL", "HE", "SPO"),
        )
        call_command("load_coverage_analysis", path)

        sources = set(CoverageAnalysisEntry.objects.values_list("source", flat=True))
        assert sources == {
            CoverageSource.ALL,
            CoverageSource.HE,
            CoverageSource.SPO,
        }

    def test_multiple_years(self, tmp_path):
        from django.core.management import call_command

        path = _make_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            years=(2026, 2027),
            sources=("ALL",),
        )
        call_command("load_coverage_analysis", path)

        assert CoverageAnalysisSummary.objects.count() == 2
        years = set(CoverageAnalysisSummary.objects.values_list("year", flat=True))
        assert years == {2026, 2027}

        # Для каждого года по 2 записи (дефицит + профицит)
        assert CoverageAnalysisEntry.objects.filter(year=2026).count() == 2
        assert CoverageAnalysisEntry.objects.filter(year=2027).count() == 2

    def test_missing_file_logs_error(self, tmp_path, capsys):
        from django.core.management import call_command

        missing = str(tmp_path / "нет_такого_файла.xlsx")
        call_command("load_coverage_analysis", missing)

        captured = capsys.readouterr()
        # В stderr должно быть сообщение о ненайденном файле
        assert (
            "не найден" in captured.err.lower() or "не найден" in captured.out.lower()
        )
        assert CoverageAnalysisSummary.objects.count() == 0
