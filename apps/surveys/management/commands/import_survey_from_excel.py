import pandas as pd
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.surveys.models import SurveyCategory, SurveyBlock, SurveyQuestion, ScaleLabel


class Command(BaseCommand):
    help = "Импорт опроса из Excel файла"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Путь к Excel файлу")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Принудительный импорт без подтверждения",
        )

    def is_block_title(self, text):
        """Определяет, является ли строка названием блока"""
        if not text:
            return False

        # Паттерны для определения названия блока
        block_patterns = [
            r"^Область\s+\d+\.",  # "Область 1.", "Область 2." и т.д.
            r"^Блок\s+\d+[:.]",  # "Блок 1:", "Блок 1."
            r"^Раздел\s+\d+[:.]",  # "Раздел 1:", "Раздел 1."
            r"^Часть\s+\d+[:.]",  # "Часть 1:", "Часть 1."
        ]

        for pattern in block_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        return False

    def handle(self, *args, **options):
        file_path = options["file_path"]
        force = options["force"]

        try:
            df = pd.read_excel(file_path, header=None, dtype=str)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка чтения файла: {e}"))
            return

        if df.empty:
            self.stdout.write(self.style.ERROR("Файл пуст"))
            return

        # Очищаем DataFrame от полностью пустых строк
        df = df.dropna(how="all")

        # Строка 1: Название опроса
        survey_name = df.iloc[0, 0]
        if pd.isna(survey_name):
            self.stdout.write(
                self.style.ERROR("Первая строка должна содержать название опроса")
            )
            return

        self.stdout.write(f"Название опроса: {survey_name}")

        # Строки 2-6: Формулировки шкалы (балл 1-5)
        # Ищем строки, которые начинаются с цифры от 1 до 5 и содержат "—"
        scale_labels = {}
        row_idx = 1
        while row_idx < len(df) and len(scale_labels) < 5:
            cell_value = df.iloc[row_idx, 0]
            if pd.notna(cell_value):
                cell_str = str(cell_value).strip()
                # Проверяем, похоже ли на формулировку шкалы
                match = re.match(r"^(\d+)\s*[—\-]\s*(.+)$", cell_str)
                if match:
                    score = int(match.group(1))
                    label = match.group(2).strip()
                    if 1 <= score <= 5:
                        scale_labels[score] = label
            row_idx += 1

        if len(scale_labels) != 5:
            self.stdout.write(
                self.style.WARNING(
                    f"Найдено {len(scale_labels)} формулировок шкалы (ожидается 5)"
                )
            )
            # Если не нашли по паттерну, пробуем следующие строки как есть
            if len(scale_labels) == 0:
                for i in range(1, 6):
                    if i < len(df):
                        label = df.iloc[i, 0]
                        if pd.notna(label):
                            scale_labels[i] = str(label).strip()

        # Пропускаем строки со шкалой и пустые строки до первого блока
        while row_idx < len(df):
            cell_value = df.iloc[row_idx, 0]
            if pd.isna(cell_value) or (
                isinstance(cell_value, str) and cell_value.strip() == ""
            ):
                row_idx += 1
            else:
                break

        # Парсинг блоков и вопросов
        blocks = {}
        current_block = None

        for i in range(row_idx, len(df)):
            cell_value = df.iloc[i, 0]

            # Пропускаем пустые строки
            if pd.isna(cell_value):
                continue

            cell_str = str(cell_value).strip()

            # Пропускаем строки, которые являются частью шкалы (если остались)
            if re.match(r"^\d+\s*[—\-]", cell_str):
                continue

            # Проверяем, является ли строка названием блока
            if self.is_block_title(cell_str):
                current_block = cell_str
                blocks[current_block] = []
                self.stdout.write(f'Найден блок: "{current_block}"')
            elif current_block is not None:
                # Это вопрос
                blocks[current_block].append(cell_str)
            else:
                # Если нет текущего блока, но есть текст — возможно, блок без маркера
                # Используем первую непустую строку как название блока
                current_block = cell_str
                blocks[current_block] = []
                self.stdout.write(f'Найден блок (без маркера): "{current_block}"')

        if not blocks:
            self.stdout.write(self.style.ERROR("Не найдено блоков с вопросами"))
            return

        total_questions = sum(len(q) for q in blocks.values())
        self.stdout.write(f"Найдено блоков: {len(blocks)}")
        self.stdout.write(f"Найдено вопросов: {total_questions}")

        # Вывод информации об импорте
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f'Будет создан опрос: "{survey_name}"')
        self.stdout.write(f"Шкала оценок:")
        for score, label in sorted(scale_labels.items()):
            self.stdout.write(f"  {score} — {label}")
        self.stdout.write(f"Блоки и вопросы:")
        for block_title, block_questions in blocks.items():
            self.stdout.write(f"  📁 {block_title} ({len(block_questions)} вопросов)")
            for q in block_questions[:3]:  # Показываем первые 3 вопроса для проверки
                self.stdout.write(f"      - {q[:50]}...")
            if len(block_questions) > 3:
                self.stdout.write(
                    f"      ... и ещё {len(block_questions) - 3} вопросов"
                )
        self.stdout.write("=" * 60)

        # Если не force, запрашиваем подтверждение (только для консоли)
        if not force:
            try:
                confirm = input("Продолжить импорт? (y/n): ")
                if confirm.lower() != "y":
                    self.stdout.write(self.style.WARNING("Импорт отменён"))
                    return
            except EOFError:
                self.stdout.write(
                    self.style.WARNING("Режим без подтверждения (импорт из админки)")
                )

        with transaction.atomic():
            # Создаём категорию опроса
            category, created = SurveyCategory.objects.get_or_create(
                name=survey_name, defaults={"description": ""}
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Создана категория: {survey_name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Категория уже существует: {survey_name}")
                )
                SurveyBlock.objects.filter(category=category).delete()
                # Удаляем старые формулировки шкалы для этого опроса
                ScaleLabel.objects.filter(category=category).delete()
                self.stdout.write(f"Удалены старые блоки, вопросы и шкала")

            # Обновляем формулировки шкалы (привязываем к категории)
            for score, label in scale_labels.items():
                ScaleLabel.objects.update_or_create(
                    category=category, scale_value=score, defaults={"label": label}
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Обновлены формулировки шкалы для опроса {survey_name}"
                )
            )

            # Создаём блоки и вопросы
            block_order = 1
            for block_title, block_questions in blocks.items():
                if not block_questions:  # Пропускаем блоки без вопросов
                    self.stdout.write(
                        self.style.WARNING(
                            f'Блок "{block_title}" не содержит вопросов, пропускаем'
                        )
                    )
                    continue

                block = SurveyBlock.objects.create(
                    category=category,
                    title=block_title,
                    order=block_order,
                    is_active=True,
                )
                self.stdout.write(f"Создан блок: {block_title} (порядок {block_order})")

                for idx, question_text in enumerate(block_questions, start=1):
                    SurveyQuestion.objects.create(
                        block=block, text=question_text, q_number=idx, is_active=True
                    )
                self.stdout.write(f"Создано вопросов в блоке: {len(block_questions)}")
                block_order += 1

        self.stdout.write(self.style.SUCCESS("\n Импорт успешно завершён!"))
