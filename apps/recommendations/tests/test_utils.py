import pytest
from django.utils import timezone
from apps.recommendations.utils import (
    has_completed_all_surveys,
    has_completed_profile,
    is_ready_for_recommendations,
)
from apps.surveys.models import SurveyCategory, SurveySession
from apps.accounts.models import EmployeeProfile

pytestmark = pytest.mark.django_db


class TestHasCompletedProfile:
    """Тесты для функции has_completed_profile"""

    def test_with_profile(self, regular_user, organization):
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )
        assert has_completed_profile(regular_user) is True

    def test_without_profile(self, regular_user):
        assert has_completed_profile(regular_user) is False


class TestHasCompletedAllSurveys:
    """Тесты для функции has_completed_all_surveys"""

    def test_no_surveys(self, regular_user):
        result = has_completed_all_surveys(regular_user)
        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["all_completed"] is False

    def test_all_surveys_completed(self, regular_user):
        survey1 = SurveyCategory.objects.create(
            name="RIASEC",
            is_active=True,
        )
        survey2 = SurveyCategory.objects.create(
            name="DigComp",
            is_active=True,
        )

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
        survey1 = SurveyCategory.objects.create(
            name="RIASEC",
            is_active=True,
        )
        survey2 = SurveyCategory.objects.create(
            name="DigComp",
            is_active=True,
        )

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

    def test_ready_with_profile_and_surveys(self, regular_user, organization):
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        survey = SurveyCategory.objects.create(
            name="RIASEC",
            is_active=True,
        )
        SurveySession.objects.create(
            user=regular_user,
            category=survey,
            status="completed",
            completed_at=timezone.now(),
        )

        assert is_ready_for_recommendations(regular_user) is True

    def test_not_ready_without_profile(self, regular_user):
        assert is_ready_for_recommendations(regular_user) is False

    def test_ready_with_profile_but_no_surveys(self, regular_user, organization):
        """Опросы не обязательны, поэтому готовность True"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )
        # Нет пройденных опросов, но готовность должна быть True
        assert is_ready_for_recommendations(regular_user) is True

    def test_not_ready_with_surveys_but_no_profile(self, regular_user):
        survey = SurveyCategory.objects.create(
            name="RIASEC",
            is_active=True,
        )
        SurveySession.objects.create(
            user=regular_user,
            category=survey,
            status="completed",
            completed_at=timezone.now(),
        )
        assert is_ready_for_recommendations(regular_user) is False
