"""
Конвертирует docx в xlsx: каждая непустая строка абзаца — отдельная строка в столбце A.

Запуск:
    python3 scripts/docx_to_xlsx.py input.docx output.xlsx
"""

import sys
from docx import Document
import pandas as pd


def convert(docx_path: str, xlsx_path: str) -> None:
    doc = Document(docx_path)
    rows = []

    for paragraph in doc.paragraphs:
        text = (paragraph.text or "").strip()
        if text:
            rows.append(text)

    # На случай, если в документе есть таблицы
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = (cell.text or "").strip()
                if text:
                    rows.append(text)

    df = pd.DataFrame({0: rows})
    df.to_excel(xlsx_path, index=False, header=False)
    print(f"Готово: {xlsx_path} ({len(rows)} строк)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python3 docx_to_xlsx.py input.docx output.xlsx")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
