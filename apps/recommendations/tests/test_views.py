import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone

from apps.recommendations.models import CourseRecommendation, RecommendationTask
from apps.surveys.models import SurveyCategory, SurveySession
from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course

pytestmark = pytest.mark.django_db


class TestMyRecommendationsView:
    """Тесты для страницы рекомендаций"""

    def test_view_requires_login(self, client):
        """Тест требования авторизации"""
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_view_without_recommendations(self, client, regular_user):
        """Тест страницы без рекомендаций"""
        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["has_recommendations"] is False
        assert len(response.context["recommendations"]) == 0

    def test_view_with_recommendations(
        self, client, regular_user, course_recommendations
    ):
        """Тест страницы с рекомендациями"""
        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["has_recommendations"] is True
        assert len(response.context["recommendations"]) == 5

    def test_view_pagination_first_page(self, client, regular_user, organization):
        """Тест первой страницы пагинации (20 записей)"""
        # Создаём 25 курсов
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
        assert response.context["paginator"].num_pages == 2

    def test_view_pagination_second_page(self, client, regular_user, organization):
        """Тест второй страницы пагинации (оставшиеся 5 записей)"""
        # Создаём 25 курсов
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
        response = client.get(url, {"page": 2})
        assert response.status_code == 200
        assert len(response.context["recommendations"]) == 5
        assert response.context["page_obj"].number == 2
        assert response.context["paginator"].num_pages == 2

    def test_view_pagination_with_less_than_page_size(
        self, client, regular_user, multiple_courses
    ):
        """Тест пагинации когда записей меньше размера страницы"""
        for i, course in enumerate(multiple_courses[:5]):
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
        assert len(response.context["recommendations"]) == 5
        assert response.context["page_obj"].number == 1
        assert response.context["paginator"].num_pages == 1

    def test_view_with_task_status(self, client, regular_user, recommendation_task):
        """Тест страницы с активной задачей"""
        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["task_status"] == recommendation_task

    def test_view_ready_for_recommendations(self, client, regular_user, organization):
        """Тест готовности к рекомендациям"""
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

        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["ready_for_recommendations"] is True


class TestGenerateRecommendationsView:
    """Тесты для генерации рекомендаций"""

    def test_generate_requires_login(self, client):
        """Тест требования авторизации"""
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_generate_not_ready(self, client, regular_user):
        """Тест генерации без готовности"""
        client.force_login(regular_user)
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("заполните анкету" in str(msg).lower() for msg in messages)
        # Проверяем редирект на страницу профиля
        assert "profile" in response.redirect_chain[0][0]

    def test_generate_already_running(
        self, client, regular_user, recommendation_task, organization
    ):
        """Тест генерации когда уже есть активная задача"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        client.force_login(regular_user)
        url = reverse("recommendations:generate_recommendations")
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("уже генерируются" in str(msg).lower() for msg in messages)

    @patch("apps.recommendations.views.generate_recommendations_for_user.delay")
    def test_generate_success(self, mock_delay, client, regular_user, organization):
        """Тест успешного запуска генерации"""
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

    @patch("apps.recommendations.views.generate_recommendations_for_user.delay")
    def test_regenerate_success(
        self, mock_delay, client, regular_user, organization, course_recommendations
    ):
        """Тест успешной перегенерации"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        assert CourseRecommendation.objects.filter(user=regular_user).count() == 5

        mock_delay.return_value.id = "test-task-456"

        client.force_login(regular_user)
        url = reverse("recommendations:regenerate_recommendations")
        response = client.post(url, follow=True)

        assert CourseRecommendation.objects.filter(user=regular_user).count() == 0

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.task_id == "test-task-456"
        assert task.status == "pending"


class TestCheckRecommendationsStatus:
    """Тесты для проверки статуса рекомендаций"""

    def test_status_pending(self, client, regular_user, recommendation_task):
        """Тест статуса pending"""
        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_status_completed(self, client, regular_user, organization):
        """Тест статуса completed"""
        # Создаём курс с организацией
        course = Course.objects.create(
            title="Тестовый курс",
            organization=organization,
            url="https://example.com/course/test",
        )
        # Создаём завершённую задачу
        RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="completed",
        )
        # Создаём рекомендацию
        CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тестовая рекомендация",
            relevance_score=0.85,
        )

        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["has_recommendations"] is True
        assert data["count"] == 1

    def test_status_failed(self, client, regular_user):
        """Тест статуса failed"""
        RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="failed",
            error_message="Ошибка API",
        )

        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Ошибка API"

    def test_status_no_task(self, client, regular_user):
        """Тест когда нет задачи"""
        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
