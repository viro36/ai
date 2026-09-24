import csv
import io
from django.contrib.admin import AdminSite
import pytest
from datetime import date
from unittest.mock import patch
from openpyxl import load_workbook

from django.contrib import admin as dj_admin
from django.urls import reverse

from apps.coverage_analysis import constants, views
from apps.coverage_analysis.admin import CoverageMethodologyAdmin, CoverageYearFilter
from apps.coverage_analysis.models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageMethodology,
    CoverageScenario,
    CoverageSource,
    CoverageBlock,
)

pytestmark = pytest.mark.django_db


# ---------- Регистрация моделей ----------
class TestRegistration:

    def test_summary_registered(self):
        assert CoverageAnalysisSummary in dj_admin.site._registry

    def test_entry_registered(self):
        assert CoverageAnalysisEntry in dj_admin.site._registry

    def test_methodology_registered(self):
        assert CoverageMethodology in dj_admin.site._registry


# ---------- Кастомные фильтры (через реальный client) ----------
class TestFilters:

    @pytest.fixture(autouse=True)
    def _login(self, client, admin_user):
        client.force_login(admin_user)

    def test_year_filter_lookups(self, summary_admin, rf, summary_optimistic_2026):
        f = CoverageYearFilter(rf.get("/"), {}, CoverageAnalysisSummary, summary_admin)
        assert list(f.lookups(rf.get("/"), summary_admin)) == [(2026, "2026")]

    def test_delta_sign_positive(self, client, entry_deficit_2026, entry_surplus_2026):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url, {"delta_sign": "positive"})
        assert response.status_code == 200
        codes = sorted(
            response.context["cl"].queryset.values_list("okz_code", flat=True)
        )
        assert codes == ["2514"]

    def test_delta_sign_negative(self, client, entry_deficit_2026, entry_surplus_2026):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url, {"delta_sign": "negative"})
        assert response.status_code == 200
        codes = sorted(
            response.context["cl"].queryset.values_list("okz_code", flat=True)
        )
        assert codes == ["7511"]

    def test_coverage_range_over(self, client, entry_deficit_2026, entry_surplus_2026):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url, {"coverage_range": "over"})
        assert response.status_code == 200
        codes = sorted(
            response.context["cl"].queryset.values_list("okz_code", flat=True)
        )
        assert codes == ["2514"]

    def test_coverage_range_low(self, client, entry_deficit_2026, entry_surplus_2026):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url, {"coverage_range": "low"})
        assert response.status_code == 200
        codes = sorted(
            response.context["cl"].queryset.values_list("okz_code", flat=True)
        )
        assert codes == ["7511"]

    def test_need_range_gt1000(self, client, entry_deficit_2026, entry_surplus_2026):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url, {"need_range": "gt1000"})
        assert response.status_code == 200
        codes = sorted(
            response.context["cl"].queryset.values_list("okz_code", flat=True)
        )
        assert codes == ["7511"]


# ---------- Методы отображения ----------
class TestDisplayMethods:

    def test_summary_coverage_display_colors(
        self, summary_admin, summary_optimistic_2026
    ):
        html = summary_admin.overall_coverage_percent_display(summary_optimistic_2026)
        assert "140.6%" in html
        assert "green" in html

    def test_summary_coverage_display_none(self, summary_admin):
        s = CoverageAnalysisSummary(year=2099, scenario=CoverageScenario.OPTIMISTIC)
        assert summary_admin.overall_coverage_percent_display(s) == "—"

    def test_entry_delta_display_negative(self, entry_admin, entry_deficit_2026):
        html = entry_admin.delta_display(entry_deficit_2026)
        assert "red" in html
        assert "-3331" in html

    def test_entry_delta_display_positive(self, entry_admin, entry_surplus_2026):
        html = entry_admin.delta_display(entry_surplus_2026)
        assert "green" in html
        assert "+795" in html

    def test_entry_delta_display_none(self, entry_admin):
        e = CoverageAnalysisEntry(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2099,
            source=CoverageSource.ALL,
            block=CoverageBlock.DEFICIT,
            okz_code="0000",
            okz_name="x",
        )
        assert entry_admin.delta_display(e) == "—"

    def test_okz_name_short_truncates(self, entry_admin, entry_deficit_2026):
        entry_deficit_2026.okz_name = "A" * 100
        out = entry_admin.okz_name_short(entry_deficit_2026)
        assert out.endswith("…")
        assert len(out) == 81


# ---------- Дата «сегодня» в changelist ----------
class TestChangelistDate:

    @patch("apps.coverage_analysis.admin.timezone.localdate")
    def test_summary_changelist_date(self, mock_localdate, client, admin_user):
        mock_localdate.return_value = date(2026, 9, 22)
        client.force_login(admin_user)
        url = reverse("admin:coverage_analysis_coverageanalysissummary_changelist")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["data_actual_date"] == "22.09.2026"

    @patch("apps.coverage_analysis.admin.timezone.localdate")
    def test_entry_changelist_date(self, mock_localdate, client, admin_user):
        mock_localdate.return_value = date(2026, 9, 22)
        client.force_login(admin_user)
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["data_actual_date"] == "22.09.2026"


# ---------- Экспорт CSV ----------
class TestExportCSV:

    def test_csv_content(self, entry_admin, rf, admin_user, entry_deficit_2026):
        request = rf.get("/")
        request.user = admin_user
        qs = CoverageAnalysisEntry.objects.filter(pk=entry_deficit_2026.pk)

        response = entry_admin.export_as_csv(request, qs)
        assert response.status_code == 200
        assert "text/csv" in response["Content-Type"]
        assert "coverage_entries.csv" in response["Content-Disposition"]

        content = response.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(content)))
        # Чистим BOM из первой строки данных (если остался)
        rows[1] = [cell.lstrip("\ufeff") for cell in rows[1]]

        assert rows[0][0] == "Год"
        assert rows[0][5] == "Код ОКЗ"
        assert rows[1][0] == "2026"
        assert rows[1][5] == "7511"
        assert rows[1][10].startswith("-3331")


# ---------- Экспорт XLSX ----------
class TestExportXLSX:

    def test_xlsx_content(self, entry_admin, rf, admin_user, entry_deficit_2026):
        request = rf.get("/")
        request.user = admin_user
        qs = CoverageAnalysisEntry.objects.filter(pk=entry_deficit_2026.pk)

        response = entry_admin.export_as_xlsx(request, qs)
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]
        assert "coverage_entries.xlsx" in response["Content-Disposition"]

        wb = load_workbook(io.BytesIO(response.content))
        ws = wb.active
        assert ws.title == "Анализ покрытия"

        assert ws.cell(row=1, column=1).value == "Год"
        assert ws.cell(row=1, column=6).value == "Код ОКЗ"

        assert ws.cell(row=2, column=1).value == 2026
        assert ws.cell(row=2, column=6).value == "7511"

        assert ws.freeze_panes == "A2"
        assert ws.auto_filter.ref is not None


# ---------- Ссылки на исходные файлы ----------
class TestDownloadFiles:

    @pytest.fixture(autouse=True)
    def _login(self, client, admin_user):
        client.force_login(admin_user)

    def test_download_files_in_context_entry(self, client):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url)
        assert response.status_code == 200
        files = response.context["download_files"]
        assert len(files) == 2

        for f in files:
            assert "scenario" in f
            assert "label" in f
            assert "filename" in f
            assert "exists" in f
            assert f["label"]  # непустой

        labels = {f["label"] for f in files}
        assert "Оптимистичный сценарий" in labels
        assert "Реалистичный сценарий" in labels

    def test_download_scenarios_are_optimistic_and_realistic(self, client):
        url = reverse("admin:coverage_analysis_coverageanalysisentry_changelist")
        response = client.get(url)
        scenarios = {f["scenario"] for f in response.context["download_files"]}
        assert scenarios == {
            CoverageScenario.OPTIMISTIC,
            CoverageScenario.REALISTIC,
        }


class TestDownloadEndpoint:

    @pytest.fixture(autouse=True)
    def _login(self, client, admin_user):
        client.force_login(admin_user)

    def test_download_unknown_scenario_404(self, client):
        url = reverse(
            "coverage_analysis:download_file",
            kwargs={"scenario": "UNKNOWN"},
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_download_existing_file(self, client, tmp_path, monkeypatch):
        fake_dir = tmp_path / "docs"
        fake_dir.mkdir()
        target = (
            fake_dir / constants.DOWNLOAD_FILES[CoverageScenario.OPTIMISTIC]["filename"]
        )
        target.write_bytes(b"fake-xlsx")

        monkeypatch.setattr(constants, "DOCS_DIR", fake_dir)
        monkeypatch.setattr(views, "DOCS_DIR", fake_dir)

        url = reverse(
            "coverage_analysis:download_file",
            kwargs={"scenario": CoverageScenario.OPTIMISTIC},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]
        assert "attachment" in response["Content-Disposition"]


class TestDownloadEndpointAnonymous:
    """Анонимный доступ к эндпоинту скачивания."""

    def test_download_anonymous_redirects(self, client):
        url = reverse(
            "coverage_analysis:download_file",
            kwargs={"scenario": CoverageScenario.OPTIMISTIC},
        )
        response = client.get(url)
        # staff_member_required редиректит на login
        assert response.status_code in (302, 403)


class TestMethodologyAdmin:

    @pytest.fixture(autouse=True)
    def _login(self, client, admin_user):
        client.force_login(admin_user)

    def test_methodology_registered(self):
        assert CoverageMethodology in dj_admin.site._registry

    def test_methodology_changelist_loads(self, client):
        url = reverse("admin:coverage_analysis_coveragemethodology_changelist")
        response = client.get(url)
        assert response.status_code == 200

    def test_text_preview_short(self, methodology_general_section):
        admin_obj = CoverageMethodologyAdmin(CoverageMethodology, AdminSite())
        html = admin_obj.text_preview(methodology_general_section)
        assert "D(ОКЗ" in html

    def test_text_preview_empty(self, db):
        obj = CoverageMethodology(scenario=None, order=1, section_title="x", text="")
        admin_obj = CoverageMethodologyAdmin(CoverageMethodology, AdminSite())
        assert admin_obj.text_preview(obj) == "—"

    def test_section_title_nan_replaced(self, db):
        obj = CoverageMethodology(scenario=None, order=1, section_title="nan", text="x")
        admin_obj = CoverageMethodologyAdmin(CoverageMethodology, AdminSite())
        assert admin_obj.section_title_short(obj) == "—"

    def test_scenario_display_general(self, db):
        obj = CoverageMethodology(scenario=None, order=1)
        admin_obj = CoverageMethodologyAdmin(CoverageMethodology, AdminSite())
        assert admin_obj.scenario_display(obj) == "Общий"
