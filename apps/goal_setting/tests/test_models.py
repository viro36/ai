import pytest
from django.db import IntegrityError
from datetime import date
from apps.goal_setting.models import Question, QuestionOption, GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestQuestionModel:
    """Тесты для модели Question"""

    def test_create_question_choice(self, test_question_choice):
        """Тест создания вопроса с выбором"""
        assert test_question_choice.text == "Какой ваш любимый язык программирования?"
        assert test_question_choice.question_type == "choice"
        assert test_question_choice.is_required is True
        assert test_question_choice.is_active is True
        assert test_question_choice.has_custom_option is True
        assert test_question_choice.custom_option_label == "Другой язык"
        assert (
            str(test_question_choice)
            == "1. Какой ваш любимый язык программирования?..."
        )

    def test_create_question_text(self, test_question_text):
        """Тест создания текстового вопроса"""
        assert test_question_text.text == "Опишите ваш опыт работы"
        assert test_question_text.question_type == "text"
        assert test_question_text.max_length == 1000

    def test_create_question_multiple_choice(self, test_question_multiple_choice):
        """Тест создания вопроса с множественным выбором"""
        assert test_question_multiple_choice.question_type == "multiple_choice"
        assert test_question_multiple_choice.is_multiple is True

    def test_create_question_date_range(self, test_question_date_range):
        """Тест создания вопроса с диапазоном дат"""
        assert test_question_date_range.question_type == "date_range"

    def test_question_str_method(self, test_question_choice):
        """Тест строкового представления вопроса"""
        expected = "1. Какой ваш любимый язык программирования?..."
        assert str(test_question_choice) == expected

    def test_question_default_values(self):
        """Тест значений по умолчанию"""
        question = Question.objects.create(
            text="Вопрос по умолчанию",
            question_type="text",
        )
        assert question.is_required is True
        assert question.is_active is True
        assert question.order == 0
        assert question.max_length == 500
        assert question.has_custom_option is False


class TestQuestionOptionModel:
    """Тесты для модели QuestionOption"""

    def test_create_option(self, test_question_choice):
        """Тест создания варианта ответа"""
        option = QuestionOption.objects.create(
            question=test_question_choice,
            value="python",
            label="Python",
            is_custom=False,
            order=0,
        )
        assert option.question == test_question_choice
        assert option.value == "python"
        assert option.label == "Python"
        assert option.is_custom is False
        # В __str__ используется question.text[:30] - обрезается до 30 символов
        # "Какой ваш любимый язык программирования?" -> 37 символов, обрезается до "Какой ваш любимый язык програм"
        expected = "Какой ваш любимый язык програм - Python"
        assert str(option) == expected

    def test_create_custom_option(self, test_question_choice):
        """Тест создания кастомного варианта ответа"""
        option = QuestionOption.objects.create(
            question=test_question_choice,
            value="custom",
            label="Другой язык",
            is_custom=True,
            order=10,
        )
        assert option.is_custom is True

    def test_option_ordering(self, test_question_choice):
        """Тест порядка вариантов"""
        for i, label in enumerate(["A", "B", "C"]):
            QuestionOption.objects.create(
                question=test_question_choice,
                value=label.lower(),
                label=label,
                order=i,
            )
        options = QuestionOption.objects.filter(question=test_question_choice)
        assert options[0].order == 0
        assert options[1].order == 1
        assert options[2].order == 2

    def test_option_related_to_question(
        self, test_question_choice, test_question_options
    ):
        """Тест связи вариантов с вопросом"""
        assert test_question_choice.options.count() == 4
        assert test_question_choice.options.first().label == "Python"


class TestGoalSettingResponseModel:
    """Тесты для модели GoalSettingResponse"""

    def test_create_response_with_option(
        self, test_user, test_question_choice, test_question_options
    ):
        """Тест создания ответа с выбранным вариантом"""
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_option=test_question_options[0],
        )
        assert response.user.username == "test_user"
        assert response.answer_option.label == "Python"
        assert response.answer_text is None
        # В __str__ используется f"{self.user} - {self.question.text[:30]}"
        # user.__str__ возвращает "Тестов Пользователь"
        # question.text[:30] обрезается до "Какой ваш любимый язык програм"
        expected = "Тестов Пользователь - Какой ваш любимый язык програм"
        assert str(response) == expected

    def test_create_response_with_text(self, test_user, test_question_text):
        """Тест создания текстового ответа"""
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_text,
            answer_text="Я работаю с Python уже 5 лет",
        )
        assert response.answer_text == "Я работаю с Python уже 5 лет"
        assert response.answer_option is None

    def test_create_response_with_date_range(self, test_user, test_question_date_range):
        """Тест создания ответа с диапазоном дат"""
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_date_range,
            answer_date_start=date(2026, 9, 1),
            answer_date_end=date(2026, 12, 31),
        )
        assert response.answer_date_start.strftime("%Y-%m-%d") == "2026-09-01"
        assert response.answer_date_end.strftime("%Y-%m-%d") == "2026-12-31"

    def test_response_unique_user_question(
        self, test_user, test_question_choice, test_question_options
    ):
        """Тест уникальности пары (user, question)"""
        GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_option=test_question_options[0],
        )
        with pytest.raises(IntegrityError):
            GoalSettingResponse.objects.create(
                user=test_user,
                question=test_question_choice,
                answer_option=test_question_options[1],
            )

    def test_response_update(
        self, test_user, test_question_choice, test_question_options
    ):
        """Тест обновления ответа"""
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_option=test_question_options[0],
        )
        assert response.answer_option.label == "Python"

        # Обновляем ответ
        response.answer_option = test_question_options[1]  # JavaScript
        response.save()
        response.refresh_from_db()
        assert response.answer_option.label == "JavaScript"

    def test_response_multiple_choice_text_storage(
        self, test_user, test_question_multiple_choice
    ):
        """Тест хранения множественного выбора в текстовом поле"""
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_multiple_choice,
            answer_text="python,javascript,java",
        )
        assert response.answer_text == "python,javascript,java"
        assert "," in response.answer_text
        assert len(response.answer_text.split(",")) == 3
