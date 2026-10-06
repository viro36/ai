"""
Общие константы и функции для разбора Excel-файлов кадровой потребности.

Вынесено отдельно, чтобы избежать циклического импорта между views.py и tasks.py.
"""

import re

import pandas as pd

SHEET_PREFIX_TO_NEED_TYPE = {
    "Общ": "Общее",
    "Замещ": "Замещение",
}

SHEET_NAME_PATTERN = re.compile(r"^(Общ|Замещ)__?(\d{4})$")


def clean_occupation_code(value):
    """Приводит код начальной группы занятий к строке ('1111.0' → '1111')."""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def safe_float(value):
    """Возвращает float или None, если значение не число."""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
