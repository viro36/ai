import pytest
from django.db import IntegrityError

from apps.mintrud.models import (
    Year,
    NeedType,
    Occupation,
    EconomicActivity,
    LaborNeed,
)

# ---------- Year ----------


@pytest.mark.django_db
def test_year_str():
    year = Year.objects.create(year=2025)
    assert str(year) == "2025"


@pytest.mark.django_db
def test_year_unique():
    Year.objects.create(year=2025)
    with pytest.raises(IntegrityError):
        Year.objects.create(year=2025)


@pytest.mark.django_db
def test_year_ordering():
    Year.objects.create(year=2027)
    Year.objects.create(year=2025)
    Year.objects.create(year=2026)
    years = list(Year.objects.values_list("year", flat=True))
    assert years == [2025, 2026, 2027]


# ---------- NeedType ----------


@pytest.mark.django_db
def test_need_type_str():
    nt = NeedType.objects.create(name="Общее")
    assert str(nt) == "Общее"


@pytest.mark.django_db
def test_need_type_unique():
    NeedType.objects.create(name="Общее")
    with pytest.raises(IntegrityError):
        NeedType.objects.create(name="Общее")


# ---------- Occupation ----------


@pytest.mark.django_db
def test_occupation_str_is_truncated_to_50_chars():
    occ = Occupation.objects.create(code="1111", name="A" * 100)
    # __str__ возвращает "1111 - AAAA...", где часть имени обрезана до 50 + "..."
    s = str(occ)
    assert s.startswith("1111 - ")
    assert s.endswith("...")
    # 20 (код) + 3 (" - ") + 50 (имя) + 3 ("...") = 79 символов
    assert len(s) == len("1111") + len(" - ") + 50 + len("...")


@pytest.mark.django_db
def test_occupation_short_name_not_truncated():
    occ = Occupation.objects.create(code="1112", name="Short")
    assert str(occ) == "1112 - Short..."


@pytest.mark.django_db
def test_occupation_unique_code():
    Occupation.objects.create(code="1111", name="A")
    with pytest.raises(IntegrityError):
        Occupation.objects.create(code="1111", name="B")


@pytest.mark.django_db
def test_occupation_ordering():
    Occupation.objects.create(code="2222", name="B")
    Occupation.objects.create(code="1111", name="A")
    codes = list(Occupation.objects.values_list("code", flat=True))
    assert codes == ["1111", "2222"]


# ---------- EconomicActivity ----------


@pytest.mark.django_db
def test_economic_activity_str():
    act = EconomicActivity.objects.create(name="Добыча полезных ископаемых")
    assert str(act) == "Добыча полезных ископаемых"


@pytest.mark.django_db
def test_economic_activity_unique_name():
    EconomicActivity.objects.create(name="X")
    with pytest.raises(IntegrityError):
        EconomicActivity.objects.create(name="X")


# ---------- LaborNeed ----------


@pytest.mark.django_db
def test_labor_need_str_contains_key_fields(labor_need):
    s = str(labor_need)
    assert "2025" in s
    assert "Общее" in s
    assert "1111" in s
    assert "100.5" in s


@pytest.mark.django_db
def test_labor_need_unique_together(
    year_2025,
    need_type_general,
    occupation_1111,
    activity_agriculture,
):
    LaborNeed.objects.create(
        year=year_2025,
        need_type=need_type_general,
        occupation=occupation_1111,
        economic_activity=activity_agriculture,
        value=1.0,
    )
    with pytest.raises(IntegrityError):
        LaborNeed.objects.create(
            year=year_2025,
            need_type=need_type_general,
            occupation=occupation_1111,
            economic_activity=activity_agriculture,
            value=2.0,
        )


@pytest.mark.django_db
def test_labor_need_different_need_type_allowed(
    year_2025,
    need_type_general,
    need_type_replacement,
    occupation_1111,
    activity_agriculture,
):
    LaborNeed.objects.create(
        year=year_2025,
        need_type=need_type_general,
        occupation=occupation_1111,
        economic_activity=activity_agriculture,
        value=1.0,
    )
    # Другой тип потребности — можно
    LaborNeed.objects.create(
        year=year_2025,
        need_type=need_type_replacement,
        occupation=occupation_1111,
        economic_activity=activity_agriculture,
        value=2.0,
    )
    assert LaborNeed.objects.count() == 2


@pytest.mark.django_db
def test_labor_need_cascade_delete_year(labor_need):
    assert LaborNeed.objects.count() == 1
    labor_need.year.delete()
    assert LaborNeed.objects.count() == 0


@pytest.mark.django_db
def test_labor_need_cascade_delete_occupation(labor_need):
    assert LaborNeed.objects.count() == 1
    labor_need.occupation.delete()
    assert LaborNeed.objects.count() == 0


@pytest.mark.django_db
def test_labor_need_updated_at_auto(labor_need):
    old = labor_need.updated_at
    labor_need.value = 999.0
    labor_need.save()
    labor_need.refresh_from_db()
    assert labor_need.updated_at >= old
    assert labor_need.value == 999.0
