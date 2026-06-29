import pytest
from apps.recommendations.models import CourseRecommendation, RecommendationTask

pytestmark = pytest.mark.django_db


class TestCourseRecommendationModel:
    """Тесты для модели CourseRecommendation"""

    def test_creation(self, regular_user, course):
        """Тест создания рекомендации"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Отличный курс",
            relevance_score=0.85,
            order=1,
        )
        assert rec.user == regular_user
        assert rec.course == course
        assert rec.reason == "Отличный курс"
        assert rec.relevance_score == 0.85
        assert rec.order == 1
        assert rec.is_viewed is False
        assert str(rec) == f"{regular_user} -> {course.title}"

    def test_default_values(self, regular_user, course):
        """Тест значений по умолчанию"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тестовая рекомендация",
        )
        assert rec.relevance_score == 0.0
        assert rec.order == 0
        assert rec.is_viewed is False

    def test_ordering(self, regular_user, multiple_courses):
        """Тест сортировки по order и relevance_score"""
        for i, course in enumerate(multiple_courses[:3]):
            CourseRecommendation.objects.create(
                user=regular_user,
                course=course,
                reason=f"Рекомендация {i}",
                relevance_score=0.9 - (i * 0.1),
                order=i,
            )

        recs = CourseRecommendation.objects.filter(user=regular_user)
        assert recs.count() == 3
        assert recs[0].order == 0
        assert recs[1].order == 1
        assert recs[2].order == 2

    def test_str_method(self, regular_user, course):
        """Тест строкового представления"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
        )
        expected = f"{regular_user} -> {course.title}"
        assert str(rec) == expected


class TestRecommendationTaskModel:
    """Тесты для модели RecommendationTask"""

    def test_creation(self, regular_user):
        """Тест создания задачи"""
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="pending",
        )
        assert task.user == regular_user
        assert task.task_id == "task-123"
        assert task.status == "pending"
        assert task.error_message is None
        assert str(task) == f"{regular_user} - pending"

    def test_status_completed(self, regular_user):
        """Тест статуса completed"""
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="pending",
        )
        task.status = "completed"
        task.save()
        task.refresh_from_db()
        assert task.status == "completed"

    def test_status_failed_with_error(self, regular_user):
        """Тест статуса failed с ошибкой"""
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="pending",
        )
        task.status = "failed"
        task.error_message = "Ошибка генерации"
        task.save()
        task.refresh_from_db()
        assert task.status == "failed"
        assert task.error_message == "Ошибка генерации"

    def test_one_to_one_user(self, regular_user):
        """Тест OneToOne связи с пользователем"""
        task1 = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-1",
            status="pending",
        )
        # Пытаемся создать вторую задачу для того же пользователя
        with pytest.raises(Exception):
            RecommendationTask.objects.create(
                user=regular_user,
                task_id="task-2",
                status="pending",
            )
