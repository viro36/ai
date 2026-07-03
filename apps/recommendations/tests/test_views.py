import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.messages import get_messages
from datetime import datetime

from apps.recommendations.models import CourseRecommendation, RecommendationTask
from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course
from apps.goal_setting.models import Question, GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestMyRecommendationsView:
    """Тесты для страницы рекомендаций"""

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

    def test_view_requires_login(self, client):
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_view_without_recommendations(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["has_recommendations"] is False
        assert len(response.context["recommendations"]) == 0

    def test_view_with_recommendations(
        self, client, regular_user, course_recommendations
    ):
        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["has_recommendations"] is True
        assert len(response.context["recommendations"]) == 5

    def test_view_pagination(self, client, regular_user, organization):
        courses = []
        for i in range(25):
            course = Course.objects.create(
                title=f"Курс {i}",
                organization=organization,
                url=f"https://example.com/course/{i}",
                is_deleted=False,
            )
            courses.append(course)

        for i, course in enumerate(courses):
            CourseRecommendation.objects.create(
                user=regular_user,
                course=course,
                reason=f"Рекомендация {i}",
                relevance_score=0.9 - (i * 0.02),
                order=i,
            )

        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context["recommendations"]) == 20
        assert response.context["page_obj"].number == 1

        response = client.get(url, {"page": 2})
        assert response.status_code == 200
        assert len(response.context["recommendations"]) == 5
        assert response.context["page_obj"].number == 2

    def test_view_ready_for_recommendations(self, client, regular_user, organization):
        """Тест готовности к рекомендациям"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["ready_for_recommendations"] is True


class TestGenerateRecommendationsView:
    """Тесты для генерации рекомендаций"""

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

    def test_generate_requires_login(self, client):
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_generate_not_ready(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("заполните анкету" in str(msg).lower() for msg in messages)

    def test_generate_already_running(
        self, client, regular_user, recommendation_task, organization
    ):
        """Тест генерации когда уже есть активная задача"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        client.force_login(regular_user)
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("уже генерируются" in str(msg).lower() for msg in messages)

    @patch("apps.recommendations.views.generate_recommendations_for_user.delay")
    def test_generate_success(self, mock_delay, client, regular_user, organization):
        """Тест успешного запуска генерации"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        mock_delay.return_value.id = "test-task-123"

        client.force_login(regular_user)
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url, follow=True)

        mock_delay.assert_called_once_with(regular_user.id)

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.task_id == "test-task-123"
        assert task.status == "pending"


class TestRegenerateRecommendationsView:
    """Тесты для перегенерации рекомендаций"""

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

    @patch("apps.recommendations.views.generate_recommendations_for_user.delay")
    def test_regenerate_success(
        self, mock_delay, client, regular_user, organization, course_recommendations
    ):
        """Тест успешной перегенерации"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        assert CourseRecommendation.objects.filter(user=regular_user).count() == 5

        mock_delay.return_value.id = "test-task-456"

        client.force_login(regular_user)
        url = reverse("recommendations:regenerate_recommendations")
        response = client.post(url, follow=True)

        # Проверяем, что старые рекомендации удалены
        assert CourseRecommendation.objects.filter(user=regular_user).count() == 0

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.task_id == "test-task-456"
        assert task.status == "pending"
