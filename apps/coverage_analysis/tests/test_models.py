import pytest
from django.db import IntegrityError

from apps.coverage_analysis.models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageScenario,
    CoverageSource,
    CoverageBlock,
)

pytestmark = pytest.mark.django_db


# ---------- CoverageAnalysisSummary ----------


class TestCoverageAnalysisSummary:

    def test_create_and_str(self, summary_optimistic_2026):
        s = summary_optimistic_2026
        assert s.pk is not None
        assert s.scenario == CoverageScenario.OPTIMISTIC
        assert s.year == 2026
        assert s.annual_closed_need == 20334
        assert "Оптимистичный" in str(s)
        assert "2026" in str(s)

    def test_default_scenario_is_optimistic(self):
        s = CoverageAnalysisSummary.objects.create(year=2027)
        assert s.scenario == CoverageScenario.OPTIMISTIC

    def test_unique_together_scenario_year(self, summary_optimistic_2026):
        with pytest.raises(IntegrityError):
            CoverageAnalysisSummary.objects.create(
                scenario=CoverageScenario.OPTIMISTIC,
                year=2026,
            )

    def test_two_scenarios_same_year_allowed(
        self, summary_optimistic_2026, summary_realistic_2026
    ):
        assert CoverageAnalysisSummary.objects.count() == 2

    def test_ordering_by_scenario_then_year(self, db):
        CoverageAnalysisSummary.objects.create(
            scenario=CoverageScenario.REALISTIC, year=2026
        )
        CoverageAnalysisSummary.objects.create(
            scenario=CoverageScenario.OPTIMISTIC, year=2027
        )
        CoverageAnalysisSummary.objects.create(
            scenario=CoverageScenario.OPTIMISTIC, year=2026
        )
        years = list(CoverageAnalysisSummary.objects.values_list("scenario", "year"))
        # OPTIMISTIC < REALISTIC, внутри — по возрастанию года
        assert years == [
            (CoverageScenario.OPTIMISTIC, 2026),
            (CoverageScenario.OPTIMISTIC, 2027),
            (CoverageScenario.REALISTIC, 2026),
        ]

    def test_nullable_fields_allowed(self, db):
        s = CoverageAnalysisSummary.objects.create(year=2030)
        assert s.annual_closed_need is None
        assert s.total_groups_with_need is None


# ---------- CoverageAnalysisEntry ----------


class TestCoverageAnalysisEntry:

    def test_create_and_str(self, entry_deficit_2026):
        e = entry_deficit_2026
        assert e.pk is not None
        assert e.okz_code == "7511"
        assert e.need == 3427
        assert e.delta == -3331
        text = str(e)
        assert "2026" in text
        assert "7511" in text

    def test_default_scenario_is_optimistic(self, db):
        e = CoverageAnalysisEntry.objects.create(
            year=2026,
            source=CoverageSource.ALL,
            block=CoverageBlock.DEFICIT,
            okz_code="0000",
            okz_name="Тест",
        )
        assert e.scenario == CoverageScenario.OPTIMISTIC

    def test_unique_together(self, entry_deficit_2026):
        with pytest.raises(IntegrityError):
            CoverageAnalysisEntry.objects.create(
                scenario=CoverageScenario.OPTIMISTIC,
                year=2026,
                source=CoverageSource.ALL,
                block=CoverageBlock.DEFICIT,
                okz_code="7511",  # тот же код ОКЗ
                okz_name="Дубль",
            )

    def test_same_okz_in_different_blocks_allowed(self, entry_deficit_2026, db):
        """Один и тот же ОКЗ может быть и в дефиците, и в профиците — это разные блоки."""
        CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.ALL,
            block=CoverageBlock.SURPLUS,
            okz_code="7511",
            okz_name="Тот же код, другой блок",
        )
        assert CoverageAnalysisEntry.objects.filter(okz_code="7511").count() == 2

    def test_same_okz_in_different_sources_allowed(
        self, entry_deficit_2026, entry_deficit_he_2026, db
    ):
        """Один и тот же ОКЗ может встречаться в ALL, HE и SPO — это разные источники."""
        same_code = CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.SPO,
            block=CoverageBlock.DEFICIT,
            okz_code="2142",
            okz_name="Тот же код, СПО",
        )
        assert same_code.pk is not None

    def test_ordering(self, db):
        CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.SPO,
            block=CoverageBlock.DEFICIT,
            position=1,
            okz_code="A",
            okz_name="A",
        )
        CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.ALL,
            block=CoverageBlock.DEFICIT,
            position=1,
            okz_code="B",
            okz_name="B",
        )
        CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.HE,
            block=CoverageBlock.DEFICIT,
            position=1,
            okz_code="C",
            okz_name="C",
        )
        sources = list(CoverageAnalysisEntry.objects.values_list("source", flat=True))
        # ALL < HE < SPO по алфавиту
        assert sources == [
            CoverageSource.ALL,
            CoverageSource.HE,
            CoverageSource.SPO,
        ]

    def test_nullable_numeric_fields(self, db):
        e = CoverageAnalysisEntry.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            year=2026,
            source=CoverageSource.ALL,
            block=CoverageBlock.DEFICIT,
            okz_code="0000",
            okz_name="Пусто",
        )
        assert e.need is None
        assert e.supply is None
        assert e.coverage_percent is None
        assert e.delta is None


class TestCoverageMethodology:

    def test_create_general_section(self, methodology_general_section):
        s = methodology_general_section
        assert s.pk is not None
        assert s.scenario is None
        assert "Закрываемая" in s.section_title
        assert "Общий" in str(s)

    def test_create_scoped_section(self, methodology_optimistic_section):
        s = methodology_optimistic_section
        assert s.scenario == CoverageScenario.OPTIMISTIC
        assert "Оптимистичный" in str(s)

    def test_unique_scenario_order(self, db):
        from django.db import IntegrityError
        from apps.coverage_analysis.models import CoverageMethodology

        CoverageMethodology.objects.create(
            scenario=CoverageScenario.OPTIMISTIC,
            order=1,
            section_title="X",
            text="",
        )
        with pytest.raises(IntegrityError):
            CoverageMethodology.objects.create(
                scenario=CoverageScenario.OPTIMISTIC,
                order=1,
                section_title="Дубль",
                text="",
            )

    def test_unique_general_order(self, db):
        from django.db import IntegrityError
        from apps.coverage_analysis.models import CoverageMethodology

        CoverageMethodology.objects.create(
            scenario=None,
            order=1,
            section_title="X",
            text="",
        )
        with pytest.raises(IntegrityError):
            CoverageMethodology.objects.create(
                scenario=None,
                order=1,
                section_title="Дубль",
                text="",
            )
