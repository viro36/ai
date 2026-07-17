import pytest
from apps.recommendations.models import (
    CourseRecommendation,
    RecommendationTask,
    SelectedCourse,
)
from django.db import IntegrityError

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

    def test_get_relevance_percent(self, regular_user, course):
        """Тест метода get_relevance_percent"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
            relevance_score=0.85,
        )
        assert rec.get_relevance_percent() == 85

        rec.relevance_score = 0.5
        rec.save()
        assert rec.get_relevance_percent() == 50

        rec.relevance_score = 0.0
        rec.save()
        assert rec.get_relevance_percent() == 0

        rec.relevance_score = 1.0
        rec.save()
        assert rec.get_relevance_percent() == 100

    def test_related_name_course(self, regular_user, course):
        """Тест related_name для курса"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
        )
        assert course.recommendations.count() == 1
        assert course.recommendations.first() == rec

    def test_related_name_user(self, regular_user, course):
        """Тест related_name для пользователя"""
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
        )
        assert regular_user.course_recommendations.count() == 1
        assert regular_user.course_recommendations.first() == rec


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
        with pytest.raises(IntegrityError):
            RecommendationTask.objects.create(
                user=regular_user,
                task_id="task-2",
                status="pending",
            )

    def test_related_name_user(self, regular_user):
        """Тест related_name для пользователя"""
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="pending",
        )
        assert regular_user.recommendation_task == task

    def test_auto_timestamps(self, regular_user):
        """Тест автоматических полей created_at и updated_at"""
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="pending",
        )
        assert task.created_at is not None
        assert task.updated_at is not None

        old_updated = task.updated_at
        task.status = "completed"
        task.save()
        task.refresh_from_db()
        assert task.updated_at > old_updated


class TestSelectedCourseModel:
    """Тесты для модели SelectedCourse"""

    def test_creation(self, regular_user, course):
        """Тест создания выбранного курса"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        assert selected.user == regular_user
        assert selected.course == course
        assert selected.created_at is not None
        assert str(selected) == f"{regular_user} -> {course.title}"

    def test_unique_together(self, regular_user, course):
        """Тест уникальности пары user + course"""
        SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        with pytest.raises(IntegrityError):
            SelectedCourse.objects.create(
                user=regular_user,
                course=course,
            )

    def test_related_name_user(self, regular_user, course):
        """Тест related_name для пользователя"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        assert regular_user.selected_courses.count() == 1
        assert regular_user.selected_courses.first() == selected

    def test_related_name_course(self, regular_user, course):
        """Тест related_name для курса"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        assert course.selected_by_users.count() == 1
        assert course.selected_by_users.first() == selected

    def test_ordering(self, regular_user, multiple_courses):
        """Тест сортировки по created_at (новые сначала)"""
        for course in multiple_courses[:3]:
            SelectedCourse.objects.create(
                user=regular_user,
                course=course,
            )

        selected = SelectedCourse.objects.filter(user=regular_user)
        assert selected.count() == 3
        # Проверяем, что сортировка по убыванию created_at
        assert selected[0].created_at >= selected[1].created_at
        assert selected[1].created_at >= selected[2].created_at
