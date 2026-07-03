import pytest
from django.utils import timezone
from datetime import datetime

from apps.recommendations.utils import (
    has_completed_all_surveys,
    has_completed_profile,
    is_ready_for_recommendations,
)
from apps.surveys.models import SurveyCategory, SurveySession
from apps.accounts.models import EmployeeProfile
from apps.goal_setting.models import Question, GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestHasCompletedProfile:
    """Тесты для функции has_completed_profile"""

    def _create_complete_profile(self, user, organization):
        EmployeeProfile.objects.create(
            user=user,
            snils="123-456-789 01",
            organization=organization,
            position="Начальник цеха",
            position_level="middle",
            gender="M",
            citizenship="Россия",
            education_level="higher",
            graduation_year=2015,
            education_institution="ВГУ",
            specialty="Программная инженерия",
            locality="Воронеж",
            municipality="Городской округ",
        )
        user.last_name = "Иванов"
        user.first_name = "Иван"
        user.birthday = datetime(1990, 1, 1).date()
        user.save()

    def test_with_complete_profile(self, regular_user, organization):
        """Тест: полностью заполненный профиль"""
        self._create_complete_profile(regular_user, organization)
        assert has_completed_profile(regular_user) is True

    def test_with_incomplete_profile(self, regular_user, organization):
        """Тест: неполный профиль (нет обязательных полей)"""
        EmployeeProfile.objects.create(
            user=regular_user,
            organization=organization,
            position="Начальник цеха",
            # position_level не заполнен
        )
        regular_user.last_name = "Иванов"
        regular_user.first_name = "Иван"
        regular_user.birthday = datetime(1990, 1, 1).date()
        regular_user.save()

        assert has_completed_profile(regular_user) is False

    def test_without_profile(self, regular_user):
        """Тест: нет профиля"""
        assert has_completed_profile(regular_user) is False


class TestHasCompletedAllSurveys:
    """Тесты для функции has_completed_all_surveys"""

    def test_no_surveys(self, regular_user):
        result = has_completed_all_surveys(regular_user)
        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["all_completed"] is False

    def test_all_surveys_completed(self, regular_user):
        survey1 = SurveyCategory.objects.create(name="RIASEC", is_active=True)
        survey2 = SurveyCategory.objects.create(name="DigComp", is_active=True)

        SurveySession.objects.create(
            user=regular_user,
            category=survey1,
            status="completed",
            completed_at=timezone.now(),
        )
        SurveySession.objects.create(
            user=regular_user,
            category=survey2,
            status="completed",
            completed_at=timezone.now(),
        )

        result = has_completed_all_surveys(regular_user)
        assert result["total"] == 2
        assert result["completed"] == 2
        assert result["all_completed"] is True

    def test_some_surveys_completed(self, regular_user):
        survey1 = SurveyCategory.objects.create(name="RIASEC", is_active=True)
        SurveyCategory.objects.create(name="DigComp", is_active=True)

        SurveySession.objects.create(
            user=regular_user,
            category=survey1,
            status="completed",
            completed_at=timezone.now(),
        )

        result = has_completed_all_surveys(regular_user)
        assert result["total"] == 2
        assert result["completed"] == 1
        assert result["all_completed"] is False


class TestIsReadyForRecommendations:
    """Тесты для функции is_ready_for_recommendations"""

    def _create_complete_profile(self, user, organization):
        EmployeeProfile.objects.create(
            user=user,
            snils="123-456-789 01",
            organization=organization,
            position="Начальник цеха",
            position_level="middle",
            gender="M",
            citizenship="Россия",
            education_level="higher",
            graduation_year=2015,
            education_institution="ВГУ",
            specialty="Программная инженерия",
            locality="Воронеж",
            municipality="Городской округ",
        )
        user.last_name = "Иванов"
        user.first_name = "Иван"
        user.birthday = datetime(1990, 1, 1).date()
        user.save()

    def _create_complete_goal_setting(self, user):
        question1 = Question.objects.create(
            text="Какая ваша цель?",
            question_type="text",
            is_active=True,
            order=1,
        )
        question2 = Question.objects.create(
            text="Что вы хотите изучить?",
            question_type="text",
            is_active=True,
            order=2,
        )

        GoalSettingResponse.objects.create(
            user=user,
            question=question1,
            answer_text="Стать экспертом в AI",
        )
        GoalSettingResponse.objects.create(
            user=user,
            question=question2,
            answer_text="Машинное обучение",
        )

    def test_ready_with_profile_and_goal(self, regular_user, organization):
        """Тест: готовность True когда есть профиль и целеполагание"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)
        assert is_ready_for_recommendations(regular_user) is True

    def test_ready_with_profile_goal_and_surveys(self, regular_user, organization):
        """Тест: готовность True когда есть профиль, целеполагание и опросы"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        survey = SurveyCategory.objects.create(name="RIASEC", is_active=True)
        SurveySession.objects.create(
            user=regular_user,
            category=survey,
            status="completed",
            completed_at=timezone.now(),
        )

        assert is_ready_for_recommendations(regular_user) is True

    def test_not_ready_without_profile(self, regular_user):
        """Тест: нет профиля -> False"""
        assert is_ready_for_recommendations(regular_user) is False

    def test_not_ready_without_goal(self, regular_user, organization):
        """Тест: нет целеполагания -> False"""
        self._create_complete_profile(regular_user, organization)
        # Не создаём целеполагание
        assert is_ready_for_recommendations(regular_user) is False

    def test_not_ready_with_incomplete_goal(self, regular_user, organization):
        """Тест: целеполагание неполное -> False"""
        self._create_complete_profile(regular_user, organization)

        # Создаём два вопроса, но отвечаем только на один
        question1 = Question.objects.create(
            text="Какая ваша цель?",
            question_type="text",
            is_active=True,
            order=1,
        )
        Question.objects.create(
            text="Что вы хотите изучить?",
            question_type="text",
            is_active=True,
            order=2,
        )

        # Отвечаем только на первый вопрос
        GoalSettingResponse.objects.create(
            user=regular_user,
            question=question1,
            answer_text="Стать экспертом",
        )

        assert is_ready_for_recommendations(regular_user) is False

    def test_not_ready_no_active_questions(self, regular_user, organization):
        """Тест: нет активных вопросов -> False"""
        self._create_complete_profile(regular_user, organization)
        # Убеждаемся, что нет активных вопросов
        Question.objects.all().delete()
        assert is_ready_for_recommendations(regular_user) is False

    def test_not_ready_without_profile_and_goal(self, regular_user):
        """Тест: нет ни профиля, ни целеполагания -> False"""
        assert is_ready_for_recommendations(regular_user) is False
