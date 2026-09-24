import pytest
from openpyxl import Workbook

from django.core.management import call_command

from apps.coverage_analysis.models import (
    CoverageMethodology,
    CoverageScenario,
)

pytestmark = pytest.mark.django_db


# ---------- Хелпер ----------
def _make_methodology_xlsx(tmp_path, filename, *, scenario_marker="Оптимистичный"):
    """
    Создаёт минимальный xlsx с листом «Методика»:
    - шапка «МЕТОДИКА РАСЧЁТА» + «СЦЕНАРИЙ: ...» + вводные абзацы (сценарный),
    - «1. Закрываемая потребность» (общий),
    - «2. Выпуск ВО» (общий),
    - «Справочно» (сценарный).
    """
    wb = Workbook()
    wb.remove(wb.active)
    ws = wb.create_sheet("Методика")

    ws.append(["МЕТОДИКА РАСЧЁТА", ""])
    ws.append([f"СЦЕНАРИЙ: {scenario_marker}", ""])
    ws.append(["", "Вводный абзац 1"])
    ws.append(["", "Вводный абзац 2"])
    ws.append(["", ""])
    ws.append(["1. Закрываемая потребность", "D(ОКЗ, год) = ..."])
    ws.append(["", "Общая потребность трактуется ..."])
    ws.append(["", ""])
    ws.append(["2. Выпуск ВО", "Из среза численности ..."])
    ws.append(["", "бакалавриат (4 г.): 4 курс -> 2026"])
    ws.append(["", ""])
    ws.append(["Справочно", "Суммарная годовая потребность: ..."])

    path = tmp_path / filename
    wb.save(path)
    return str(path)


# ---------- Тесты ----------
class TestLoadMethodologyCommand:

    def test_general_and_scoped_sections(self, tmp_path):
        path = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            scenario_marker="ТРУДОУСТРОЙСТВО ПО СПЕЦИАЛЬНОСТИ",
        )
        call_command("load_coverage_methodology", path)

        # Общие разделы: 1 и 2
        general = CoverageMethodology.objects.filter(scenario__isnull=True)
        assert general.count() == 2
        titles = {s.section_title for s in general}
        assert titles == {"Закрываемая потребность", "Выпуск ВО"}
        nums = {s.section_number for s in general}
        assert nums == {"1", "2"}

        # Сценарные OPTIMISTIC: «Шапка методики» и «Справочно» = 2
        scoped = CoverageMethodology.objects.filter(
            scenario=CoverageScenario.OPTIMISTIC
        )
        assert scoped.count() == 2
        titles = {s.section_title for s in scoped}
        assert titles == {"Шапка методики", "Справочно"}

    def test_general_sections_not_duplicated_on_reload(self, tmp_path):
        path_opt = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            scenario_marker="ТРУДОУСТРОЙСТВО ПО СПЕЦИАЛЬНОСТИ",
        )
        path_real = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            scenario_marker="С УЧЁТОМ МИГРАЦИИ",
        )

        call_command("load_coverage_methodology", path_opt, path_real)

        # Общие разделы не должны дублироваться — их ровно 2
        general = CoverageMethodology.objects.filter(scenario__isnull=True)
        assert general.count() == 2

        # У каждого сценария — свои сценарные разделы (по 2: шапка + справочно)
        opt = CoverageMethodology.objects.filter(scenario=CoverageScenario.OPTIMISTIC)
        real = CoverageMethodology.objects.filter(scenario=CoverageScenario.REALISTIC)
        assert opt.count() == 2
        assert real.count() == 2

        # Всего в БД: 2 общих + 2 OPTIMISTIC + 2 REALISTIC = 6
        assert CoverageMethodology.objects.count() == 6

    def test_reload_same_scenario_replaces(self, tmp_path):
        path = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            scenario_marker="ТРУДОУСТРОЙСТВО ПО СПЕЦИАЛЬНОСТИ",
        )

        call_command("load_coverage_methodology", path)
        # 2 общих + 2 сценарных OPTIMISTIC = 4
        assert CoverageMethodology.objects.count() == 4

        call_command("load_coverage_methodology", path)
        # После повторной загрузки — снова 4, не 8
        assert CoverageMethodology.objects.count() == 4

        general = CoverageMethodology.objects.filter(scenario__isnull=True)
        assert general.count() == 2

        scoped = CoverageMethodology.objects.filter(
            scenario=CoverageScenario.OPTIMISTIC
        )
        assert scoped.count() == 2

    def test_scenario_filter(self, tmp_path):
        path_opt = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            scenario_marker="ТРУДОУСТРОЙСТВО ПО СПЕЦИАЛЬНОСТИ",
        )
        path_real = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            scenario_marker="С УЧЁТОМ МИГРАЦИИ",
        )

        call_command(
            "load_coverage_methodology",
            path_opt,
            path_real,
            scenario="OPTIMISTIC",
        )

        # REALISTIC не загружен
        assert (
            CoverageMethodology.objects.filter(
                scenario=CoverageScenario.REALISTIC
            ).count()
            == 0
        )

        # OPTIMISTIC загружен: 2 сценарных
        assert (
            CoverageMethodology.objects.filter(
                scenario=CoverageScenario.OPTIMISTIC
            ).count()
            == 2
        )

        # Общие тоже загружены (из первого подходящего файла)
        assert CoverageMethodology.objects.filter(scenario__isnull=True).count() == 2

    def test_missing_sheet_logs_warning(self, tmp_path):
        wb = Workbook()
        wb.remove(wb.active)
        wb.create_sheet("Что-то другое")
        path = tmp_path / "no_methodology.xlsx"
        wb.save(path)

        call_command("load_coverage_methodology", str(path))
        assert CoverageMethodology.objects.count() == 0

    def test_scenario_filter_skips_mismatched(self, tmp_path, capsys):
        """При --scenario OPTIMISTIC файл реалистичного сценария пропускается."""
        path_opt = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами "
            "(все по выпускники устраиваются по специальности).xlsx",
            scenario_marker="ТРУДОУСТРОЙСТВО ПО СПЕЦИАЛЬНОСТИ",
        )
        path_real = _make_methodology_xlsx(
            tmp_path,
            "Анализ покрытия потребности кадрами"
            "(доля выпускников устраивается не по специальности или мигрируют).xlsx",
            scenario_marker="С УЧЁТОМ МИГРАЦИИ",
        )

        call_command(
            "load_coverage_methodology",
            path_opt,
            path_real,
            scenario="OPTIMISTIC",
        )

        captured = capsys.readouterr()
        assert "Пропускаем" in captured.out
        assert "REALISTIC" in captured.out
