import io
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from openpyxl import Workbook

from apps.mintrud.models import Occupation, EconomicActivity


def _make_xlsx(rows, header_row_3, header_row_4):
    """
    Собирает .xlsx в памяти.

    :param rows: список строк данных (row[0..N])
    :param header_row_3: строка шапки (iloc[3])
    :param header_row_4: строка заголовков видов деятельности (iloc[4])
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Общ__2025"

    # Строки 0..2 — произвольные заголовки
    ws.append(["Сведения", None, None])
    ws.append(["1 В соответствии...", None, None])
    ws.append(["2 В соответствии...", None, None])

    # Строка 3 — шапка
    ws.append(header_row_3)

    # Строка 4 — заголовки видов деятельности
    ws.append(header_row_4)

    # Строки 5+ — данные
    for r in rows:
        ws.append(r)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


@pytest.mark.django_db
def test_load_references_creates_activities_and_occupations(tmp_path):
    # 6 колонок: код группы, код начальной, имя, вид1, вид2, вид3
    header_row_3 = [
        None,
        "Код начальной группы занятий1",
        "Наименование начальной группы занятий1",
        "Раздел вида экономической деятельности2",
        None,
        None,
    ]
    header_row_4 = [
        None,
        None,
        None,
        "Сельское, лесное хозяйство",
        "Добыча полезных ископаемых",
        "Обрабатывающие производства",
    ]
    rows = [
        [11, 1111, "Руководители", 0, 0, 0],
        [11, 1112, "Руководители представители", 1.5, 2.5, 3.5],
    ]

    xlsx_buf = _make_xlsx(rows, header_row_3, header_row_4)

    # Сохраняем во временный файл, т.к. openpyxl-буфер read_excel не всегда глотает
    file_path = tmp_path / "test.xlsx"
    file_path.write_bytes(xlsx_buf.getvalue())

    call_command("load_references", str(file_path))

    assert EconomicActivity.objects.count() == 3
    assert Occupation.objects.count() == 2

    occ = Occupation.objects.get(code="1111")
    assert occ.name == "Руководители"

    activity = EconomicActivity.objects.get(name="Добыча полезных ископаемых")
    assert activity.name == "Добыча полезных ископаемых"


@pytest.mark.django_db
def test_load_references_skips_existing(tmp_path):
    # Создаём заранее один Occupation и один EconomicActivity
    Occupation.objects.create(code="1111", name="Старое имя")
    EconomicActivity.objects.create(name="Сельское, лесное хозяйство")

    header_row_3 = [None, "Код", "Наименование", "Раздел", None, None]
    header_row_4 = [
        None,
        None,
        None,
        "Сельское, лесное хозяйство",
        "Добыча полезных ископаемых",
        "Обрабатывающие производства",
    ]
    rows = [
        [11, 1111, "Новое имя", 0, 0, 0],
    ]
    xlsx_buf = _make_xlsx(rows, header_row_3, header_row_4)
    file_path = tmp_path / "test.xlsx"
    file_path.write_bytes(xlsx_buf.getvalue())

    call_command("load_references", str(file_path))

    # Не продублировались
    assert EconomicActivity.objects.count() == 3
    assert Occupation.objects.count() == 1
    # Имя обновилось
    assert Occupation.objects.get(code="1111").name == "Новое имя"


@pytest.mark.django_db
def test_load_references_raises_on_empty(tmp_path):
    # Файл с недостаточным числом строк
    wb = Workbook()
    ws = wb.active
    ws.title = "Общ__2025"
    ws.append(["x"])  # одна строка

    file_path = tmp_path / "empty.xlsx"
    wb.save(file_path)

    with pytest.raises(CommandError):
        call_command("load_references", str(file_path))
