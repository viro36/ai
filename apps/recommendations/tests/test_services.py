import pytest
from apps.accounts.models import EmployeeProfile
from apps.recommendations.services import DeepSeekRecommendationService


@pytest.mark.django_db
class TestDeepSeekServiceUnemployed:
    """Тесты для сервиса с безработным"""

    def test_profile_includes_unemployed_flag(self, test_employee_user):
        """Профиль содержит флаг is_unemployed"""
        EmployeeProfile.objects.filter(user=test_employee_user).delete()

        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="777-888-999 00",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
            is_svo_participant=True,
        )

        service = DeepSeekRecommendationService(test_employee_user)
        profile = service.get_user_profile()

        assert profile["user_info"]["is_unemployed"] is True
        assert profile["user_info"]["is_svo_participant"] is True

    def test_prompt_for_unemployed(self, test_employee_user):
        """Промпт содержит блок 'Безработный'"""
        EmployeeProfile.objects.filter(user=test_employee_user).delete()

        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="555-666-777 88",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )

        service = DeepSeekRecommendationService(test_employee_user)
        prompt = service.prepare_prompt()

        assert "Безработный" in prompt
        assert "ОСОБЕННОСТИ ДЛЯ БЕЗРАБОТНЫХ" in prompt

    def test_prompt_for_working_svo(self, test_employee_user, organization):
        """Промпт содержит статус 'Работающий (участник СВО)'"""
        EmployeeProfile.objects.filter(user=test_employee_user).delete()

        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="666-777-888 99",
            organization=organization,
            position="Инженер",
            position_level="specialist",
            is_svo_participant=True,
        )

        service = DeepSeekRecommendationService(test_employee_user)
        prompt = service.prepare_prompt()

        assert "Работающий (участник СВО)" in prompt
        assert "ОСОБЕННОСТИ ДЛЯ БЕЗРАБОТНЫХ" not in prompt
