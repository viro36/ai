import pytest

from apps.mintrud.models import (
    Year,
    NeedType,
    Occupation,
    EconomicActivity,
    LaborNeed,
)


@pytest.fixture
def year_2025(db):
    return Year.objects.create(year=2025)


@pytest.fixture
def need_type_general(db):
    return NeedType.objects.create(name="Общее")


@pytest.fixture
def need_type_replacement(db):
    return NeedType.objects.create(name="Замещение")


@pytest.fixture
def occupation_1111(db):
    return Occupation.objects.create(
        code="1111",
        name="Руководители федеральных и региональных органов "
        "законодательной власти и их аппаратов, депутаты "
        "законодательных собраний",
    )


@pytest.fixture
def occupation_1112(db):
    return Occupation.objects.create(
        code="1112",
        name="Руководители (представители) федеральных и региональных "
        "органов исполнительной и судебной власти и их аппаратов",
    )


@pytest.fixture
def activity_agriculture(db):
    return EconomicActivity.objects.create(
        name="Сельское, лесное хозяйство, охота, рыболовство и рыбоводство"
    )


@pytest.fixture
def activity_mining(db):
    return EconomicActivity.objects.create(name="Добыча полезных ископаемых")


@pytest.fixture
def labor_need(
    db,
    year_2025,
    need_type_general,
    occupation_1111,
    activity_agriculture,
):
    return LaborNeed.objects.create(
        year=year_2025,
        need_type=need_type_general,
        occupation=occupation_1111,
        economic_activity=activity_agriculture,
        value=100.5,
        source_file="test.xlsx",
    )
