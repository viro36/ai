import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from apps.recommendations.tasks import generate_recommendations_for_user
from apps.recommendations.models import CourseRecommendation, RecommendationTask
from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course
from apps.goal_setting.models import Question, GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestGenerateRecommendationsTask:
    """Тесты для задачи генерации рекомендаций"""

    def _create_complete_profile(self, user, organization):
        """Хелпер для создания полного профиля"""
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
        """Хелпер для создания полного целеполагания"""
        # Создаём активные вопросы
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

        # Создаём ответы
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

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_success(self, mock_service, regular_user, organization):
        """Тест успешной генерации рекомендаций"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        course = Course.objects.create(
            title="Тестовый курс",
            organization=organization,
            url="https://example.com/course/test",
        )

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = [
            {
                "course_id": course.id,
                "reason": "Отличный курс",
                "relevance_score": 85,
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
        assert rec.relevance_score == 0.85

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_no_recommendations(self, mock_service, regular_user, organization):
        """Тест когда нет рекомендаций"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

        mock_instance = MagicMock()
        mock_instance.get_recommendations.return_value = []
        mock_service.return_value = mock_instance

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "success"
        assert result["created"] == 0

        rec = CourseRecommendation.objects.filter(user=regular_user).first()
        assert rec is None

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.status == "completed"

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_existing_recommendations(
        self, mock_service, regular_user, organization
    ):
        """Тест когда уже есть рекомендации"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

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

        new_rec = CourseRecommendation.objects.filter(user=regular_user).first()
        assert new_rec.course == course2
        assert new_rec.reason == "Новая рекомендация"
        assert new_rec.relevance_score == 0.9

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_invalid_course_id(
        self, mock_service, regular_user, organization
    ):
        """Тест с несуществующим ID курса"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

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

        assert CourseRecommendation.objects.filter(user=regular_user).count() == 0
        assert result["status"] == "success"
        assert result["created"] == 0

        task = RecommendationTask.objects.filter(user=regular_user).first()
        assert task is not None
        assert task.status == "completed"

    @patch("apps.recommendations.tasks.DeepSeekRecommendationService")
    def test_task_with_error(self, mock_service, regular_user, organization):
        """Тест с ошибкой в сервисе"""
        self._create_complete_profile(regular_user, organization)
        self._create_complete_goal_setting(regular_user)

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

    def test_task_profile_not_complete(self, regular_user, organization):
        """Тест когда профиль не заполнен"""
        # Создаём неполный профиль
        EmployeeProfile.objects.create(
            user=regular_user,
            organization=organization,
            position="Начальник цеха",
            # position_level не заполнен
        )

        result = generate_recommendations_for_user(regular_user.id)

        assert result["status"] == "error"
        assert "заполнил анкету" in result["error"]
