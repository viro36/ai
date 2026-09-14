"""
Загрузка профстандартов, ОТФ и связей с ФГОС из Excel-файла
"ВО_СПО_Холланд_Профстандарт_ОТФ.xlsx".

Запуск:
    python manage.py load_standards_otf
    python manage.py load_standards_otf /path/to/file.xlsx
    python manage.py load_standards_otf --clear-otf
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from apps.surveys.models import (
    RiasecCodeInterpretation,
    ProfessionalStandard,
    GeneralizedLaborFunction,
    EducationProgram,
    ProfessionalStandardProgram,
)

DEFAULT_DOC = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "ВО_СПО_Холланд_Профстандарт_ОТФ.xlsx"
)

EDU_MAP = {"ВО": "VO", "СПО": "SPO"}

# Код ПС в Excel: "10.028", "40.136" — две цифры, точка, три цифры
PS_CODE_RE = re.compile(r"^(\d{2}\.\d{3})\s+(.+)$")


class Command(BaseCommand):
    help = "Загружает профстандарты, ОТФ и связи с ФГОС из Excel (3-й файл)"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            nargs="?",
            type=str,
            default=str(DEFAULT_DOC),
            help=f"Путь к .xlsx (по умолчанию: {DEFAULT_DOC})",
        )
        parser.add_argument("--sheet", type=str, default=None)
        parser.add_argument(
            "--clear-otf",
            action="store_true",
            help="Удалить существующие ОТФ перед импортом",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file"]).expanduser().resolve()
        if not file_path.exists():
            raise CommandError(f"Файл не найден: {file_path}")

        self.stdout.write(f"Читаю: {file_path}")
        wb = load_workbook(file_path, data_only=True)
        ws = wb[options["sheet"]] if options["sheet"] else wb.active

        headers = [cell.value for cell in ws[1]]
        col = {name: idx for idx, name in enumerate(headers) if name}

        # --- Обязательные колонки ---
        required = [
            "Уровень образования",
            "Код направления",
            "Наименование направления",
            "Коды Холланда ВО",
        ]
        for r in required:
            if r not in col:
                raise CommandError(f"Нет колонки: {r}. Найдены: {list(col)}")

        # --- Колонки профстандартов и ОТФ (1..5) ---
        ps_cols = []  # [(order, idx_ps, idx_otf)]
        for n in range(1, 6):
            col_ps = f"{n}. профстандарт"
            col_otf = f"{n}. ОТФ (раздел II)"
            if col_ps in col:
                ps_cols.append((n, col[col_ps], col.get(col_otf)))

        if not ps_cols:
            raise CommandError("Не найдены колонки с профстандартами")

        # --- Кэш кодов Холланда ---
        riasec_cache = {r.code: r for r in RiasecCodeInterpretation.objects.all()}
        if not riasec_cache:
            self.stdout.write(
                self.style.WARNING(
                    "Коды RIASEC не найдены. Сначала: python manage.py load_riasec_codes"
                )
            )

        # --- Чистка ОТФ (опционально) ---
        if options["clear_otf"]:
            deleted, _ = GeneralizedLaborFunction.objects.all().delete()
            self.stdout.write(f"Удалено ОТФ: {deleted}")

        # --- Счётчики ---
        created_ps = updated_ps = 0
        created_otf = updated_otf = 0
        created_programs = 0
        created_links = 0
        skipped = 0

        for row_idx, row in enumerate(
            ws.iter_rows(min_row=2, values_only=True), start=2
        ):
            if not row or not row[col["Код направления"]]:
                continue

            edu_raw = str(row[col["Уровень образования"]] or "").strip()
            edu = EDU_MAP.get(edu_raw)
            if not edu:
                self.stderr.write(f"[{row_idx}] Неизвестный уровень: {edu_raw!r}")
                skipped += 1
                continue

            # =========================================================
            # ФГОС (направление)
            # =========================================================
            prog_code = str(row[col["Код направления"]]).strip()[:50]
            prog_name = str(row[col["Наименование направления"]]).strip()

            program, was_created = EducationProgram.objects.update_or_create(
                code=prog_code,
                education_level=edu,
                defaults={
                    "name": prog_name,
                    "is_active": True,
                },
            )
            created_programs += int(was_created)

            # =========================================================
            # Профстандарты (1..5)
            # =========================================================
            for order, col_ps, col_otf in ps_cols:
                if col_ps >= len(row) or not row[col_ps]:
                    continue

                ps_raw = str(row[col_ps]).strip()

                # Берём только первую строку ячейки —
                # иногда в колонке ПС оказываются ОТФ, склеенные с названием ПС
                ps_first_line = ps_raw.split("\n", 1)[0].strip()

                # Жёстко проверяем формат "XX.XXX Название"
                m = PS_CODE_RE.match(ps_first_line)
                if not m:
                    self.stderr.write(
                        f"[{row_idx}] Пропущен ПС (не найден код вида XX.XXX): "
                        f"{ps_first_line[:80]!r}"
                    )
                    skipped += 1
                    continue

                ps_code, ps_name = m.group(1), m.group(2).strip()

                ps, was_created = ProfessionalStandard.objects.update_or_create(
                    code=ps_code,
                    education_level=edu,
                    defaults={"name": ps_name, "is_active": True},
                )
                created_ps += int(was_created)
                updated_ps += int(not was_created)

                # --- Привязка RIASEC-кодов к ПС ---
                # В 3-м файле колонка "Коды Холланда ВО" относится к направлению,
                # но мы привязываем её к ПС, т.к. это единственная доступная привязка.
                riasec_raw = str(row[col["Коды Холланда ВО"]] or "").strip()
                if riasec_raw and riasec_cache:
                    codes = [
                        c.strip().upper()
                        for c in re.split(r"[/,;]", riasec_raw)
                        if c.strip()
                    ]
                    found = [riasec_cache[c] for c in codes if c in riasec_cache]
                    if found:
                        ps.riasec_codes.set(found)

                # --- Связь ПС <-> ФГОС ---
                _, link_created = ProfessionalStandardProgram.objects.update_or_create(
                    professional_standard=ps,
                    education_program=program,
                    defaults={"order": order},
                )
                created_links += int(link_created)

                # --- ОТФ ---
                if col_otf is not None and col_otf < len(row) and row[col_otf]:
                    otf_text = str(row[col_otf]).strip()
                    otf_lines = [
                        line.strip() for line in otf_text.split("\n") if line.strip()
                    ]
                    for otf_order, otf_name in enumerate(otf_lines, start=1):
                        otf_code = self._make_otf_code(otf_order)

                        _, otf_created = (
                            GeneralizedLaborFunction.objects.update_or_create(
                                professional_standard=ps,
                                code=otf_code,
                                defaults={
                                    "name": otf_name,
                                    "order": otf_order,
                                    "is_active": True,
                                },
                            )
                        )
                        created_otf += int(otf_created)
                        updated_otf += int(not otf_created)

        # --- Итоговый отчёт ---
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== Импорт завершён ===\n"
                f"Профстандарты:  создано {created_ps}, обновлено {updated_ps}\n"
                f"ОТФ:            создано {created_otf}, обновлено {updated_otf}\n"
                f"ФГОС:           создано {created_programs}\n"
                f"Связей ПС-ФГОС: создано {created_links}\n"
                f"Пропущено строк: {skipped}"
            )
        )

    def _make_otf_code(self, n):
        """1 - 'A', 2 - 'B', ..., 27 - 'AA'."""
        result = ""
        while n > 0:
            n, rem = divmod(n - 1, 26)
            result = chr(65 + rem) + result
        return result
