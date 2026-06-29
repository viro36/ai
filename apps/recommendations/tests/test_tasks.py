import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from apps.recommendations.tasks import generate_recommendations_for_user
from apps.recommendations.models import CourseRecommendation, RecommendationTask
from apps.surveys.models import SurveyCategory, SurveySession
from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course

pytestmark = pytest.mark.django_db


class TestGenerateRecommendationsTask:
    """Тесты для задачи генерации рекомендаций"""

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_success(self, mock_service, regular_user, organization):
        """Тест успешной генерации рекомендаций"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        course = Course.objects.create(
            title="Тестовый курс",
            organization=organization,
            url="https://example.com/course/test",
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

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = [
            {
                "course_id": course.id,
                "reason": "Отличный курс",
                "relevance_score": 85,  # 85% (будет преобразован в 0.85)
            }
        ]
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "success"
        assert result["created"] == 1

        rec = CourseRecommendation.objects.filter(user=regular_user).first()
        assert rec is not None
        assert rec.course == course
        assert rec.reason == "Отличный курс"
        # В задаче relevance_score делится на 100, если > 1
        assert rec.relevance_score == 0.85

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_no_recommendations(self, mock_service, regular_user, organization):
        """Тест когда нет рекомендаций"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = []
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "success"
        assert result["created"] == 0

        rec = CourseRecommendation.objects.filter(user=regular_user).first()
        assert rec is None

        # Проверяем, что задача создана со статусом completed
        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.status == "completed"

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_existing_recommendations(
        self, mock_service, regular_user, organization
    ):
        """Тест когда уже есть рекомендации"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        # Старый курс
        course1 = Course.objects.create(
            title="Старый курс",
            organization=organization,
            url="https://example.com/course/old",
        )
        CourseRecommendation.objects.create(
            user=regular_user,
            course=course1,
            reason="Старая рекомендация",
            relevance_score=0.5,
        )
        assert CourseRecommendation.objects.filter(user=regular_user).count() == 1

        # Новый курс
        course2 = Course.objects.create(
            title="Новый курс",
            organization=organization,
            url="https://example.com/course/new",
        )

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = [
            {
                "course_id": course2.id,
                "reason": "Новая рекомендация",
                "relevance_score": 90,
            }
        ]
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "success"
        assert result["created"] == 1
        assert CourseRecommendation.objects.filter(user=regular_user).count() == 1

        # Проверяем, что старая рекомендация удалена
        new_rec = CourseRecommendation.objects.filter(user=regular_user).first()
        assert new_rec.course == course2
        assert new_rec.reason == "Новая рекомендация"
        assert new_rec.relevance_score == 0.9

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_invalid_course_id(
        self, mock_service, regular_user, organization
    ):
        """Тест с несуществующим ID курса"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = [
            {
                "course_id": 99999,
                "reason": "Несуществующий курс",
                "relevance_score": 85,
            }
        ]
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        # Рекомендация не должна создаться
        assert CourseRecommendation.objects.filter(user=regular_user).count() == 0
        assert result["status"] == "success"
        assert result["created"] == 0

        # Проверяем, что задача создана со статусом completed
        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.status == "completed"

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_error(self, mock_service, regular_user, organization):
        """Тест с ошибкой в сервисе"""
        EmployeeProfile.objects.create(
            user=regular_user,
            position="Начальник цеха",
            position_level="middle",
            organization=organization,
        )

        mock_instance = MagicMock()
        mock_instance.get_recommendations.side_effect = Exception("API Error")
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "error"
        assert result["error"] == "API Error"

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.status == "failed"
        assert task.error_message == "API Error"

    def test_task_user_not_found(self):
        """Тест когда пользователь не найден"""
        result = generate_recommendations_for_user(99999)
        assert result["status"] == "error"
        assert result["error"] == "User not found"
