import re

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Position
from apps.organizations.models import OrganizationType
from apps.surveys.models import (
    SurveyBlock,
    SurveyCategory,
    SurveyQuestion,
    SurveyQuestionOption,
)

# ---------- Регулярные выражения ----------

WORK_PATTERN = re.compile(r"^Диагностическая\s+работа\s+(\d+)", re.IGNORECASE)
TASK_PATTERN = re.compile(r"^Задание\s+(\d+\.\d+)\.", re.IGNORECASE)
VARIANT_PATTERN = re.compile(r"^Вариант\s+([АБВГ])", re.IGNORECASE)
ITEM_PATTERN = re.compile(r"^([АБВГ])(\d+)[\)\.]\s*(.+)$")

# Ключ: «Ключ: 2 балла — А2, Б3, В2, Г2. 0 баллов — остальные варианты.»
KEY_PATTERN = re.compile(r"Ключ:\s*[^—\-–]*[—\-–]\s*(.+)", re.IGNORECASE)
KEY_ITEM_PATTERN = re.compile(r"([АБВГ])(\d+)", re.IGNORECASE)


class Command(BaseCommand):
    help = "Импорт диагностического комплекта руководителя ОО из Excel"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Путь к xlsx-файлу")
        parser.add_argument(
            "--organization-type",
            type=str,
            default="Общее образование",
            help="Название типа организации для привязки опроса",
        )
        parser.add_argument(
            "--positions",
            nargs="*",
            default=[],
            help="Названия должностей (из справочника Position)",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        org_type_name = options["organization_type"]
        position_names = options["positions"]

        # ---------- Читаем Excel ----------
        try:
            df = pd.read_excel(file_path, header=None, dtype=str)
        except Exception as e:
            raise CommandError(f"Ошибка чтения файла: {e}")

        df = df.dropna(how="all")
        if df.empty:
            raise CommandError("Файл пуст")

        survey_name = str(df.iloc[0, 0]).strip()
        self.stdout.write(f"Название опроса: {survey_name}")

        # ---------- Парсинг ----------
        # Структура:
        # works = {
        #   "Диагностическая работа 1": {
        #       "subtitle": "Управление образовательной деятельностью и качеством (ТФ B/01.7)",
        #       "tasks": {
        #           "1.1": {
        #               "base_text": "...",
        #               "variants": {"А": [(1, "…"), (2, "…"), ...], ...},
        #               "correct": {"А2", "Б3", "В2", "Г2"},
        #           },
        #           ...
        #       },
        #   },
        #   ...
        # }
        works = {}
        current_work = None
        current_task = None
        current_variant = None
        expect_subtitle = False

        # Строки, которые нужно игнорировать
        skip_markers = (
            "общие положения",
            "шкала работы",
            "интегральная оценка",
            "валидность",
            "время:",
            "максимум:",
            "формат заданий",
            "оценка:",
            "ситуация:",
            "вопрос:",
        )

        for i in range(len(df)):
            text = str(df.iloc[i, 0]).strip()
            if not text:
                continue
            low = text.lower()
            if any(m in low for m in skip_markers):
                continue

            # --- Работа ---
            m = WORK_PATTERN.match(text)
            if m:
                current_work = text
                works.setdefault(
                    current_work,
                    {"subtitle": "", "tasks": {}},
                )
                current_task = None
                current_variant = None
                expect_subtitle = True
                continue

            # --- Название работы (следующая строка после «Диагностическая работа N») ---
            if expect_subtitle and current_work:
                works[current_work]["subtitle"] = text
                expect_subtitle = False
                continue

            # --- Задание ---
            m = TASK_PATTERN.match(text)
            if m and current_work:
                current_task = m.group(1)
                works[current_work]["tasks"].setdefault(
                    current_task,
                    {"base_text": "", "variants": {}, "correct": set()},
                )
                current_variant = None
                continue

            # --- Вариант ---
            m = VARIANT_PATTERN.match(text)
            if m and current_work and current_task:
                current_variant = m.group(1).upper()
                works[current_work]["tasks"][current_task]["variants"].setdefault(
                    current_variant, []
                )
                continue

            # --- Подпункт (А1, Б2, …) ---
            m = ITEM_PATTERN.match(text)
            if m and current_work and current_task and current_variant:
                letter, num, body = m.group(1).upper(), int(m.group(2)), m.group(3)
                if letter == current_variant:
                    task_data = works[current_work]["tasks"][current_task]
                    task_data["variants"][current_variant].append((num, body.strip()))
                    if not task_data["base_text"]:
                        task_data["base_text"] = body.strip()
                continue

            # --- Ключ ---
            if low.startswith("ключ:") and current_work and current_task:
                m = KEY_PATTERN.search(text)
                if m:
                    for letter, num in KEY_ITEM_PATTERN.findall(m.group(1)):
                        works[current_work]["tasks"][current_task]["correct"].add(
                            f"{letter.upper()}{num}"
                        )
                continue

        if not works:
            raise CommandError("Не удалось распознать ни одной работы")

        # ---------- Проверка типа организации и должностей ----------
        try:
            org_type = OrganizationType.objects.get(name=org_type_name)
        except OrganizationType.DoesNotExist:
            raise CommandError(f"Тип организации «{org_type_name}» не найден")

        positions = []
        if position_names:
            positions = list(Position.objects.filter(name__in=position_names))
            missing = set(position_names) - {p.name for p in positions}
            if missing:
                self.stdout.write(
                    self.style.WARNING(f"Не найдены должности: {', '.join(missing)}")
                )

        # ---------- Сохранение ----------
        with transaction.atomic():
            category, created = SurveyCategory.objects.get_or_create(
                name=survey_name,
                defaults={
                    "description": "Диагностический комплект руководителя ОО",
                    "target_user_types": ["employee"],
                    "target_organization_type": org_type,
                },
            )

            # Обновляем ограничения аудитории в любом случае
            category.target_user_types = ["employee"]
            category.target_organization_type = org_type
            category.save()

            if not created:
                SurveyBlock.objects.filter(category=category).delete()
                self.stdout.write("Старые блоки удалены")

            if positions:
                category.target_positions.set(positions)
                self.stdout.write(f"Должности: {', '.join(p.name for p in positions)}")

            block_order = 1
            for work_title, data in works.items():
                subtitle = data.get("subtitle", "")
                tasks = data.get("tasks", {})

                if not tasks:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Работа «{work_title}» не содержит заданий, пропускаем"
                        )
                    )
                    continue

                block = SurveyBlock.objects.create(
                    category=category,
                    title=work_title,
                    subtitle=subtitle or None,
                    order=block_order,
                    is_active=True,
                )

                q_number = 1
                for task_code, task_data in tasks.items():
                    variants = task_data["variants"]
                    correct = task_data["correct"]

                    if not variants:
                        continue

                    base_text = task_data.get("base_text") or f"Задание {task_code}"

                    question = SurveyQuestion.objects.create(
                        block=block,
                        text=f"Задание {task_code}. {base_text[:200]}",
                        q_number=q_number,
                        is_active=True,
                    )

                    option_order = 0
                    for letter in ("А", "Б", "В", "Г"):
                        for num, body in variants.get(letter, []):
                            code = f"{letter}{num}"
                            SurveyQuestionOption.objects.create(
                                question=question,
                                group=letter,
                                text=f"{letter}{num}) {body}",
                                is_correct=(code in correct),
                                order=option_order,
                            )
                            option_order += 1

                    q_number += 1

                self.stdout.write(
                    f"  Блок «{work_title}» ({subtitle[:60]}): "
                    f"{q_number - 1} заданий, "
                    f"{SurveyQuestionOption.objects.filter(question__block=block).count()} опций"
                )
                block_order += 1

        self.stdout.write(self.style.SUCCESS("Импорт завершён"))
