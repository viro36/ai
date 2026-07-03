import pytest
from apps.goal_setting.utils import (
    has_completed_goal_setting,
    get_goal_setting_progress,
)
from apps.goal_setting.models import GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestGoalSettingUtils:
    """Тесты для утилит целеполагания"""

    def test_has_completed_goal_setting_true(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: все вопросы отвечены"""
        for question in [
            test_question_choice,
            test_question_text,
            test_question_multiple_choice,
            test_question_date_range,
        ]:
            GoalSettingResponse.objects.create(
                user=test_user, question=question, answer_text="Ответ"
            )
        assert has_completed_goal_setting(test_user) is True

    def test_has_completed_goal_setting_false(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: не все вопросы отвечены"""
        GoalSettingResponse.objects.create(
            user=test_user, question=test_question_choice, answer_text="Ответ"
        )
        assert has_completed_goal_setting(test_user) is False

    def test_has_completed_goal_setting_no_answers(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: нет ответов, но есть вопросы"""
        # Вопросы существуют, но ответов нет
        assert has_completed_goal_setting(test_user) is False

    def test_get_goal_setting_progress(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: прогресс с 2 ответами из 4"""
        questions = [test_question_choice, test_question_text]
        for q in questions:
            GoalSettingResponse.objects.create(
                user=test_user, question=q, answer_text="Ответ"
            )
        result = get_goal_setting_progress(test_user)
        assert result["total"] == 4
        assert result["answered"] == 2
        assert result["progress"] == 50
        assert result["is_complete"] is False

    def test_get_goal_setting_progress_empty(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: прогресс без ответов, но вопросы существуют"""
        result = get_goal_setting_progress(test_user)
        assert result["total"] == 4
        assert result["answered"] == 0
        assert result["progress"] == 0
        assert result["is_complete"] is False

    def test_get_goal_setting_progress_complete(
        self,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: прогресс 100%"""
        for q in [
            test_question_choice,
            test_question_text,
            test_question_multiple_choice,
            test_question_date_range,
        ]:
            GoalSettingResponse.objects.create(
                user=test_user, question=q, answer_text="Ответ"
            )
        result = get_goal_setting_progress(test_user)
        assert result["progress"] == 100
        assert result["is_complete"] is True
