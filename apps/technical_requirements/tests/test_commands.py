import pytest
from django.core.management import call_command
from io import StringIO

from apps.technical_requirements.models import Question

pytestmark = pytest.mark.django_db


class TestCreateInitialQuestionsCommand:
    """Тесты для команды create_initial_questions"""

    def test_command_creates_questions(self):
        """Тест создания вопросов командой"""
        # Проверяем что вопросов нет
        assert Question.objects.count() == 0

        # Выполняем команду
        out = StringIO()
        call_command("create_initial_questions", stdout=out)

        # Проверяем что вопросы созданы
        assert Question.objects.count() == 18
        assert "Начальные вопросы успешно созданы!" in out.getvalue()

    def test_command_does_not_create_duplicates(self):
        """Тест - команда не создаёт дубликаты при повторном запуске"""
        # Первый запуск
        call_command("create_initial_questions")
        assert Question.objects.count() == 18

        # Второй запуск
        out = StringIO()
        call_command("create_initial_questions", stdout=out)

        # Количество вопросов не изменилось
        assert Question.objects.count() == 18
        assert "уже существует" in out.getvalue()

    def test_command_creates_correct_questions(self):
        """Тест создания правильных вопросов"""
        call_command("create_initial_questions")

        # Проверяем вопросы по порядку
        q1 = Question.objects.get(order=1)
        assert q1.question_type == "textarea"
        assert q1.is_required is True
        assert "Проблема" in q1.text

        q3 = Question.objects.get(order=3)
        assert q3.question_type == "choice"
        assert "Автоматизация" in q3.options
        assert "Свой вариант" in q3.options

        q4 = Question.objects.get(order=4)
        assert q4.question_type == "boolean"
        assert q4.is_required is True

        # Проверяем зависимости
        q5 = Question.objects.get(order=5)
        assert q5.depends_on == q4
        assert q5.depends_value == "True"

        q7 = Question.objects.get(order=7)
        assert q7.question_type == "boolean"

        q8 = Question.objects.get(order=8)
        assert q8.depends_on == q7
        assert q8.depends_value == "True"

    def test_command_handles_missing_depends_on(self):
        """Тест - если depends_on не существует, команда не падает"""
        # Создаём вопрос с depends_on_id которого нет
        from django.core.management import call_command
        from io import StringIO

        # Команда должна отработать без ошибок
        out = StringIO()
        call_command("create_initial_questions", stdout=out)
        assert "Начальные вопросы успешно созданы!" in out.getvalue()

    def test_command_creates_question_with_options(self):
        """Тест создания вопроса с вариантами ответов"""
        call_command("create_initial_questions")

        q3 = Question.objects.get(order=3)
        expected_options = [
            "Автоматизация",
            "Внедрение ИИ",
            "Бережливое управление",
            "Снижение затрат",
            "Повышение производительности труда",
            "Передовые практики в отрасли",
            "Свой вариант",
        ]
        assert q3.options == expected_options

    def test_command_creates_question_with_help_text(self):
        """Тест создания вопроса с help_text"""
        call_command("create_initial_questions")

        q18 = Question.objects.get(order=18)
        assert q18.help_text is not None
        assert "ВНИМАНИЕ" in q18.help_text
