import pytest
from django.core.management import call_command
from apps.goal_setting.models import Question, QuestionOption

pytestmark = pytest.mark.django_db


class TestSeedGoalSettingQuestionsCommand:
    """Тесты для команды seed_goal_setting_questions"""

    def test_command_creates_questions(self):
        """Тест: команда создаёт все 6 вопросов с опциями"""
        # Выполняем команду
        call_command("seed_goal_setting_questions")

        # Проверяем количество вопросов
        assert Question.objects.count() == 6

        # Проверяем первый вопрос (choice)
        q1 = Question.objects.get(order=1)
        assert q1.text == "В связи с чем Вам сейчас необходимо обучение?"
        assert q1.question_type == "choice"
        assert q1.is_required is True
        assert q1.has_custom_option is True
        assert q1.options.count() == 7  # 6 обычных + 1 кастомный

        # Проверяем второй вопрос (text)
        q2 = Question.objects.get(order=2)
        assert q2.question_type == "text"
        assert q2.max_length == 1000

        # Проверяем пятый вопрос (multiple_choice)
        q5 = Question.objects.get(order=5)
        assert q5.question_type == "multiple_choice"
        assert q5.is_multiple is True
        assert q5.options.count() == 4  # 4 варианта без кастомного

        # Проверяем шестой вопрос (date_range)
        q6 = Question.objects.get(order=6)
        assert q6.question_type == "date_range"

        # Проверяем, что все опции созданы
        assert QuestionOption.objects.count() == 7 + 4  # 7 для 1-го, 4 для 5-го

    def test_command_is_idempotent(self):
        """Тест: повторный запуск команды не создаёт дубликаты"""
        call_command("seed_goal_setting_questions")
        first_count = Question.objects.count()

        call_command("seed_goal_setting_questions")
        second_count = Question.objects.count()

        assert first_count == second_count
        assert first_count == 6

    def test_command_creates_custom_option(self):
        """Тест: для вопроса 1 создаётся кастомная опция"""
        call_command("seed_goal_setting_questions")
        q1 = Question.objects.get(order=1)
        custom_option = q1.options.get(is_custom=True)
        assert custom_option.value == "custom"
        assert custom_option.label == "Свой вариант"
