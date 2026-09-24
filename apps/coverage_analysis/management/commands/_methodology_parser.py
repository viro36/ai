import re

import pandas as pd

# «1. Закрываемая потребность», «2. Выпуск ВО», ...
SECTION_RE = re.compile(r"^(\d+)\.\s*(.+)$")

# Строки шапки (до первого `N. ...`)
HEADER_KEYWORDS = ("МЕТОДИКА", "СЦЕНАРИЙ")


def _clean(value):
    """Приводит ячейку Excel к строке, убивая NaN/None."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def parse_methodology_sheet(df, scenario):
    """
    Возвращает список dict-ов для CoverageMethodology.

    Логика:
    - Шапка файла (МЕТОДИКА РАСЧЁТА, СЦЕНАРИЙ: ...) сворачивается
      в один сценарный раздел «Шапка методики».
    - Раздел начинается со строки вида «N. Название» (общий раздел).
      Его текст собирается из последующих строк, где A пустая, B заполнена.
    - «Справочно» и другие ненумерованные заголовки после шапки —
      сценарные разделы.
    """
    values = df.values.tolist()

    sections = []
    header_lines = []

    current_number = ""
    current_title = None
    current_lines = []
    in_header = True

    def flush_section():
        nonlocal current_number, current_title, current_lines
        if current_title is None:
            return
        is_general = bool(current_number)
        sections.append(
            {
                "scenario": None if is_general else scenario,
                "section_number": current_number,
                "section_title": current_title,
                "text": "\n".join(current_lines),
            }
        )
        current_number = ""
        current_title = None
        current_lines = []

    for row in values:
        a = _clean(row[0] if len(row) > 0 else None)
        b = _clean(row[1] if len(row) > 1 else None)

        # Пустая строка — граница блока
        if not a and not b:
            continue

        # Строка с непустым A
        if a:
            m = SECTION_RE.match(a)

            # Ещё в шапке и это не «N. ...» — копим в шапку
            if in_header and not m:
                header_lines.append(a)
                if b:
                    header_lines.append(b)
                continue

            # Первый «N. ...» — шапка закончилась
            if in_header:
                in_header = False
                if header_lines:
                    sections.append(
                        {
                            "scenario": scenario,
                            "section_number": "",
                            "section_title": "Шапка методики",
                            "text": "\n".join(header_lines),
                        }
                    )
                    header_lines = []

            # Закрываем предыдущий раздел
            flush_section()

            # Открываем новый
            if m:
                current_number = m.group(1)
                current_title = m.group(2).strip()
            else:
                # Ненумерованный заголовок после шапки (например, «Справочно»)
                current_number = ""
                current_title = a

            current_lines = []
            if b:
                current_lines.append(b)
            continue

        # Строка без A, но с B
        if b:
            if in_header:
                header_lines.append(b)
            else:
                current_lines.append(b)

    # Закрываем последний раздел
    if in_header and header_lines:
        sections.append(
            {
                "scenario": scenario,
                "section_number": "",
                "section_title": "Шапка методики",
                "text": "\n".join(header_lines),
            }
        )
    else:
        flush_section()

    for i, s in enumerate(sections, start=1):
        s["order"] = i

    return sections
