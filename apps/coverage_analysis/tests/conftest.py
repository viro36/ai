import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.coverage_analysis.models import (
    CoverageAnalysisSummary,
    CoverageAnalysisEntry,
    CoverageScenario,
    CoverageSource,
    CoverageBlock,
)
from apps.coverage_analysis.admin import (
    CoverageAnalysisSummaryAdmin,
    CoverageAnalysisEntryAdmin,
)


# ---------- Инфраструктурные фикстуры ----------
@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin", password="pass", email="a@a.ru"
    )


@pytest.fixture
def summary_admin(admin_site):
    return CoverageAnalysisSummaryAdmin(CoverageAnalysisSummary, admin_site)


@pytest.fixture
def entry_admin(admin_site):
    return CoverageAnalysisEntryAdmin(CoverageAnalysisEntry, admin_site)


# ---------- Фикстуры моделей: сводки ----------
@pytest.fixture
def summary_optimistic_2026(db):
    """Оптимистичный сценарий, 2026 год."""
    return CoverageAnalysisSummary.objects.create(
        scenario=CoverageScenario.OPTIMISTIC,
        year=2026,
        annual_closed_need=20334,
        graduate_supply=28585,
        overall_coverage_percent=140.6,
        cat_closes=11,
        cat_surplus=61,
        cat_partial=8,
        cat_not_closes=93,
        cat_not_closes_no_programs=56,
        cat_sector_shrink=91,
        cat_career_growth=12,
        cat_no_prof_training=14,
        cat_no_need=89,
        total_groups_with_need=255,
    )


@pytest.fixture
def summary_realistic_2026(db):
    """Реалистичный сценарий, 2026 год."""
    return CoverageAnalysisSummary.objects.create(
        scenario=CoverageScenario.REALISTIC,
        year=2026,
        annual_closed_need=20334,
        graduate_supply=12046,
        overall_coverage_percent=59.2,
        total_groups_with_need=255,
    )


# ---------- Фикстуры моделей: записи ----------
@pytest.fixture
def entry_deficit_2026(db):
    """Дефицит, все источники, 2026."""
    return CoverageAnalysisEntry.objects.create(
        scenario=CoverageScenario.OPTIMISTIC,
        year=2026,
        source=CoverageSource.ALL,
        block=CoverageBlock.DEFICIT,
        position=1,
        okz_code="7511",
        okz_name=(
            "Обработчики и изготовители мясных, рыбных " "и других продуктов питания"
        ),
        need=3427,
        supply=96,
        coverage_percent=2.8,
        delta=-3331,
    )


@pytest.fixture
def entry_surplus_2026(db):
    """Профицит, все источники, 2026."""
    return CoverageAnalysisEntry.objects.create(
        scenario=CoverageScenario.OPTIMISTIC,
        year=2026,
        source=CoverageSource.ALL,
        block=CoverageBlock.SURPLUS,
        position=1,
        okz_code="2514",
        okz_name="Программисты приложений",
        need=73,
        supply=867,
        coverage_percent=1194.3,
        delta=795,
    )


@pytest.fixture
def entry_deficit_he_2026(db):
    """Дефицит, только ВО, 2026."""
    return CoverageAnalysisEntry.objects.create(
        scenario=CoverageScenario.OPTIMISTIC,
        year=2026,
        source=CoverageSource.HE,
        block=CoverageBlock.DEFICIT,
        position=1,
        okz_code="2142",
        okz_name="Инженеры по гражданскому строительству",
        need=1220,
        supply=357,
        coverage_percent=29.3,
        delta=-863,
    )


@pytest.fixture
def entry_deficit_spo_2026(db):
    """Дефицит, только СПО, 2026."""
    return CoverageAnalysisEntry.objects.create(
        scenario=CoverageScenario.OPTIMISTIC,
        year=2026,
        source=CoverageSource.SPO,
        block=CoverageBlock.DEFICIT,
        position=1,
        okz_code="8331",
        okz_name="Водители пассажирского транспорта",
        need=1219,
        supply=20,
        coverage_percent=1.6,
        delta=-1199,
    )
