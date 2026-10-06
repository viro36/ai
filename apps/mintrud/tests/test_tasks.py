import pytest
from openpyxl import Workbook

from apps.mintrud.models import (
    Year,
    NeedType,
    Occupation,
    EconomicActivity,
    LaborNeed,
)
from apps.mintrud.tasks import process_labor_needs_file


def _make_xlsx(sheets: dict, tmp_path):
    """
    Собирает .xlsx с несколькими листами.

    :param sheets: {"Общ__2025": {"rows": [...], "h3": [...], "h4": [...]}, ...}
    :return: путь к файлу (str)
    """
    wb = Workbook()
    # Удаляем дефолтный лист, если он не нужен
    default = wb.active
    wb.remove(default)

    for sheet_name, payload in sheets.items():
        ws = wb.create_sheet(title=sheet_name)
        # Строки 0..2 — произвольные «шапки документа»
        ws.append(["Сведения", None, None])
        ws.append(["1 В соответствии...", None, None])
        ws.append(["2 В соответствии...", None, None])
        # Строка 3 — заголовок таблицы
        ws.append(payload["h3"])
        # Строка 4 — заголовки видов деятельности
        ws.append(payload["h4"])
        # Строки 5+ — данные
        for r in payload["rows"]:
            ws.append(r)

    file_path = tmp_path / "test.xlsx"
    wb.save(file_path)
    return str(file_path)


# ---------- базовые сценарии ----------


@pytest.mark.django_db
def test_task_processes_one_sheet(tmp_path):
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел", None],
            "h4": [
                None,
                None,
                None,
                "Сельское хозяйство",
                "Добыча полезных ископаемых",
            ],
            "rows": [
                [11, 1111, "Руководители", 100.5, 0],
                [11, 1112, "Руководители представители", 0, 200.0],
            ],
        }
    }
    path = _make_xlsx(sheets, tmp_path)

    result = process_labor_needs_file(path, source_name="test.xlsx")

    assert result["processed_sheets"] == 1
    assert result["total_rows"] == 4  # 2 строки × 2 вида деятельности
    assert result["skipped_sheets"] == []

    assert Year.objects.filter(year=2025).exists()
    assert NeedType.objects.filter(name="Общее").exists()
    assert Occupation.objects.count() == 2
    assert EconomicActivity.objects.count() == 2
    assert LaborNeed.objects.count() == 4

    # Проверим конкретное значение
    ln = LaborNeed.objects.get(
        year__year=2025,
        need_type__name="Общее",
        occupation__code="1111",
        economic_activity__name="Сельское хозяйство",
    )
    assert ln.value == 100.5
    assert ln.source_file == "test.xlsx"


@pytest.mark.django_db
def test_task_handles_multiple_sheets_and_need_types(tmp_path):
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "A", 10]],
        },
        "Замещ__2026": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "A", 20]],
        },
    }
    path = _make_xlsx(sheets, tmp_path)

    result = process_labor_needs_file(path, source_name="test.xlsx")

    assert result["processed_sheets"] == 2
    assert result["total_rows"] == 2

    assert Year.objects.count() == 2
    assert NeedType.objects.count() == 2
    assert LaborNeed.objects.count() == 2

    v_2025 = LaborNeed.objects.get(year__year=2025).value
    v_2026 = LaborNeed.objects.get(year__year=2026).value
    assert v_2025 == 10
    assert v_2026 == 20


@pytest.mark.django_db
def test_task_skips_sheets_with_wrong_names(tmp_path):
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "A", 10]],
        },
        "Sheet1": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "B", 99]],
        },
        "Замещ__abcd": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "C", 99]],
        },
    }
    path = _make_xlsx(sheets, tmp_path)

    result = process_labor_needs_file(path, source_name="test.xlsx")

    assert result["processed_sheets"] == 1
    assert set(result["skipped_sheets"]) == {"Sheet1", "Замещ__abcd"}
    assert LaborNeed.objects.count() == 1


# ---------- skip_zeros ----------


@pytest.mark.django_db
def test_task_skip_zeros(tmp_path):
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел", None],
            "h4": [None, None, None, "Активность 1", "Активность 2"],
            "rows": [[11, 1111, "A", 0, 5]],
        }
    }
    path = _make_xlsx(sheets, tmp_path)

    # Без skip_zeros — две записи
    result = process_labor_needs_file(path, source_name="test.xlsx", skip_zeros=False)
    assert result["total_rows"] == 2

    LaborNeed.objects.all().delete()

    # С skip_zeros — только одна (нулевая пропущена)
    result = process_labor_needs_file(path, source_name="test.xlsx", skip_zeros=True)
    assert result["total_rows"] == 1
    assert LaborNeed.objects.get().value == 5


# ---------- идемпотентность ----------


@pytest.mark.django_db
def test_task_is_idempotent(tmp_path):
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "A", 10]],
        }
    }
    path = _make_xlsx(sheets, tmp_path)

    process_labor_needs_file(path, source_name="v1.xlsx")
    process_labor_needs_file(path, source_name="v2.xlsx")

    assert LaborNeed.objects.count() == 1
    ln = LaborNeed.objects.get()
    # source_file перезаписался
    assert ln.source_file == "v2.xlsx"


# ---------- ошибки ----------


@pytest.mark.django_db
def test_task_raises_if_file_missing():
    with pytest.raises(FileNotFoundError):
        process_labor_needs_file("/tmp/does-not-exist.xlsx", source_name="x.xlsx")


@pytest.mark.django_db
def test_task_uses_media_root_for_relative_path(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    sheets = {
        "Общ__2025": {
            "h3": [None, "Код", "Наименование", "Раздел"],
            "h4": [None, None, None, "Сельское хозяйство"],
            "rows": [[11, 1111, "A", 42]],
        }
    }
    _make_xlsx(sheets, tmp_path)  # создаёт tmp_path/test.xlsx

    # Относительный путь — таска сама приклеит MEDIA_ROOT
    result = process_labor_needs_file("test.xlsx", source_name="test.xlsx")
    assert result["total_rows"] == 1
