import pytest

from apps.mintrud.parsing import (
    SHEET_NAME_PATTERN,
    clean_occupation_code,
    safe_float,
)

# ---------- clean_occupation_code ----------


@pytest.mark.parametrize(
    "value,expected",
    [
        (1111.0, "1111"),
        (1111, "1111"),
        ("1111", "1111"),
        ("  1111  ", "1111"),
        (None, ""),
        (float("nan"), ""),
        ("nan", "nan"),  # не число, но строка остаётся как есть
        ("abc", "abc"),
    ],
)
def test_clean_occupation_code(value, expected):
    assert clean_occupation_code(value) == expected


# ---------- safe_float ----------


@pytest.mark.parametrize(
    "value,expected",
    [
        (100, 100.0),
        (100.5, 100.5),
        ("100.5", 100.5),
        ("0", 0.0),
        (None, None),
        (float("nan"), None),
        ("abc", None),
        ("", None),
    ],
)
def test_safe_float(value, expected):
    result = safe_float(value)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected)


# ---------- SHEET_NAME_PATTERN ----------


@pytest.mark.parametrize(
    "sheet_name,expected",
    [
        ("Общ__2025", ("Общ", "2025")),
        ("Общ__2032", ("Общ", "2032")),
        ("Замещ__2026", ("Замещ", "2026")),
        ("Общ_2025", ("Общ", "2025")),  # одно подчёркивание
        (
            "Общ__2025 ",
            ("Общ", "2025"),
        ),  # пробел в конце — но regex не матчит, см. ниже
        ("Общ__25", None),  # не 4 цифры
        ("Общ__20251", None),  # 5 цифр
        ("Other__2025", None),
        ("Общ", None),
        ("", None),
    ],
)
def test_sheet_name_pattern(sheet_name, expected):
    m = SHEET_NAME_PATTERN.match(sheet_name.strip())
    if expected is None:
        assert m is None
    else:
        assert m.groups() == expected
