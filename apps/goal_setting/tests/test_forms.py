import pytest
from datetime import date
from apps.goal_setting.forms import GoalSettingForm
from apps.goal_setting.models import GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestGoalSettingForm:
    """Тесты для формы GoalSettingForm"""

    def test_form_initialization_no_responses(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест инициализации формы без существующих ответов"""
        form = GoalSettingForm(test_user)
        assert "question_1" in form.fields
        assert "question_2" in form.fields
        assert "question_3" in form.fields
        assert "question_4_start" in form.fields
        assert "question_4_end" in form.fields
        assert form.fields["question_1"].initial is None
        assert form.fields["question_2"].initial is None
        assert form.fields["question_3"].initial is None

    def test_form_initialization_with_existing_responses(
        self, test_user, test_question_choice, test_question_text, test_question_options
    ):
        """Тест инициализации формы с существующими ответами"""
        # Создаём ответ
        GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_option=test_question_options[0],
        )
        GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_text,
            answer_text="Тестовый текстовый ответ",
        )

        form = GoalSettingForm(test_user)
        assert form.fields["question_1"].initial == "python"
        assert form.fields["question_2"].initial == "Тестовый текстовый ответ"

    def test_form_invalid_without_required_fields(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: форма невалидна, если обязательные поля пустые"""
        data = {}  # все поля пустые
        form = GoalSettingForm(test_user, data)
        assert not form.is_valid()
        assert "question_1" in form.errors
        assert "question_2" in form.errors
        assert "question_3" in form.errors
        assert "question_4_start" in form.errors
        assert "question_4_end" in form.errors

    def test_form_valid_for_choice(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: валидные данные для choice вопроса"""
        data = {
            "question_1": "python",  # выбор стандартного варианта
            "question_2": "Текстовый ответ",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        form = GoalSettingForm(test_user, data)
        assert form.is_valid(), form.errors
        form.save()
        response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_choice
        )
        assert response.answer_option.value == "python"
        assert response.answer_text is None

    def test_form_valid_for_custom_choice(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: валидные данные с кастомным вариантом"""
        data = {
            "question_1": "custom",
            "question_1_custom": "Мой любимый язык - Ruby",
            "question_2": "Текстовый ответ",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        form = GoalSettingForm(test_user, data)
        assert form.is_valid(), form.errors
        form.save()
        response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_choice
        )
        assert response.answer_text == "Мой любимый язык - Ruby"
        assert response.answer_option.is_custom is True
        assert response.answer_option.value == f"custom_{test_question_choice.id}"

    def test_form_valid_for_multiple_choice(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: валидные данные для multiple_choice"""
        data = {
            "question_1": "python",
            "question_2": "Текстовый ответ",
            "question_3": ["python", "javascript"],  # множественный выбор
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        form = GoalSettingForm(test_user, data)
        assert form.is_valid(), form.errors
        form.save()
        response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_multiple_choice
        )
        assert response.answer_text == "python,javascript"
        assert response.answer_option is None

    def test_form_valid_for_text(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: валидные данные для text вопроса"""
        data = {
            "question_1": "python",
            "question_2": "Я работаю с Python уже 5 лет",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        form = GoalSettingForm(test_user, data)
        assert form.is_valid(), form.errors
        form.save()
        response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_text
        )
        assert response.answer_text == "Я работаю с Python уже 5 лет"

    def test_form_valid_for_date_range(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: валидные данные для date_range"""
        data = {
            "question_1": "python",
            "question_2": "Текстовый ответ",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        form = GoalSettingForm(test_user, data)
        assert form.is_valid(), form.errors
        form.save()
        response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_date_range
        )
        assert response.answer_date_start == date(2026, 9, 1)
        assert response.answer_date_end == date(2026, 12, 31)
