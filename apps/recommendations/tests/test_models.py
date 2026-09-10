from django.utils import timezone
import pytest
from apps.recommendations.models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
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


class TestApprovedSelectedCourseModel:
    """Тесты для модели ApprovedSelectedCourse"""

    def test_creation(self, regular_user, course, admin_user):
        """Тест создания одобрения"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        approved = ApprovedSelectedCourse.objects.create(
            selected_course=selected,
            status="approved",
            approved_by=admin_user,
            approved_at=timezone.now(),
            comment="Отличный выбор!",
        )
        assert approved.selected_course == selected
        assert approved.status == "approved"
        assert approved.approved_by == admin_user
        assert approved.comment == "Отличный выбор!"
        assert (
            str(approved)
            == f"{regular_user} -> {course.title}: {approved.get_status_display()}"
        )

    def test_status_choices(self, regular_user, multiple_courses):
        """Тест выбора статуса - используем разные курсы"""
        for i, status in enumerate(["pending", "approved", "rejected"]):
            selected = SelectedCourse.objects.create(
                user=regular_user,
                course=multiple_courses[i],  # разные курсы
            )
            approved = ApprovedSelectedCourse.objects.create(
                selected_course=selected,
                status=status,
            )
            assert approved.status == status

    def test_default_status(self, regular_user, course):
        """Тест статуса по умолчанию"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        approved = ApprovedSelectedCourse.objects.create(
            selected_course=selected,
        )
        assert approved.status == "pending"

    def test_one_to_one_relation(self, regular_user, course):
        """Тест OneToOne связи с SelectedCourse"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        approved = ApprovedSelectedCourse.objects.create(
            selected_course=selected,
            status="approved",
        )
        assert selected.approval == approved
        assert approved.selected_course == selected

    def test_related_name_selected_course(self, regular_user, course):
        """Тест related_name с SelectedCourse"""
        selected = SelectedCourse.objects.create(
            user=regular_user,
            course=course,
        )
        approved = ApprovedSelectedCourse.objects.create(
            selected_course=selected,
        )
        assert selected.approval == approved

    def test_str_method_with_different_statuses(self, regular_user, multiple_courses):
        """Тест строкового представления для разных статусов - используем разные курсы"""
        for i, status in enumerate(["pending", "approved", "rejected"]):
            selected = SelectedCourse.objects.create(
                user=regular_user,
                course=multiple_courses[i],  # разные курсы
            )
            approved = ApprovedSelectedCourse.objects.create(
                selected_course=selected,
                status=status,
            )
            assert approved.get_status_display() in str(approved)

    def test_ordering(self, regular_user, multiple_courses):
        """Тест сортировки (новые сначала) - используем разные курсы"""
        selected1 = SelectedCourse.objects.create(
            user=regular_user,
            course=multiple_courses[0],
        )
        selected2 = SelectedCourse.objects.create(
            user=regular_user,
            course=multiple_courses[1],
        )
        approved1 = ApprovedSelectedCourse.objects.create(
            selected_course=selected1,
            status="pending",
        )
        approved2 = ApprovedSelectedCourse.objects.create(
            selected_course=selected2,
            status="approved",
        )
        approvals = ApprovedSelectedCourse.objects.all()
        assert approvals[0].created_at >= approvals[1].created_at


class TestEmployerRecommendationModel:
    """Тесты для модели EmployerRecommendation"""

    def test_creation(self, employer_user, regular_user, course):
        """Тест создания рекомендации от работодателя"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
            reason="Рекомендую этот курс для повышения квалификации",
        )
        assert rec.employer == employer_user
        assert rec.employee == regular_user
        assert rec.course == course
        assert rec.reason == "Рекомендую этот курс для повышения квалификации"
        assert rec.is_viewed is False
        assert str(rec) == f"{employer_user} -> {regular_user} -> {course.title}"

    def test_default_values(self, employer_user, regular_user, course):
        """Тест значений по умолчанию"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        assert rec.reason is None
        assert rec.is_viewed is False

    def test_ordering(self, employer_user, regular_user, multiple_courses):
        """Тест сортировки по created_at (новые сначала)"""
        for course in multiple_courses[:3]:
            EmployerRecommendation.objects.create(
                employer=employer_user,
                employee=regular_user,
                course=course,
            )

        recs = EmployerRecommendation.objects.filter(
            employer=employer_user, employee=regular_user
        )
        assert recs.count() == 3
        # Проверяем, что сортировка по убыванию created_at
        assert recs[0].created_at >= recs[1].created_at
        assert recs[1].created_at >= recs[2].created_at

    def test_unique_together(self, employer_user, regular_user, course):
        """Тест уникальности пары employer + employee + course"""
        EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        with pytest.raises(IntegrityError):
            EmployerRecommendation.objects.create(
                employer=employer_user,
                employee=regular_user,
                course=course,
            )

    def test_related_name_employer(self, employer_user, regular_user, course):
        """Тест related_name для работодателя"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        assert employer_user.employer_recommendations.count() == 1
        assert employer_user.employer_recommendations.first() == rec

    def test_related_name_employee(self, employer_user, regular_user, course):
        """Тест related_name для работника"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        assert regular_user.employee_recommendations.count() == 1
        assert regular_user.employee_recommendations.first() == rec

    def test_related_name_course(self, employer_user, regular_user, course):
        """Тест related_name для курса"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        assert course.employer_recommendations.count() == 1
        assert course.employer_recommendations.first() == rec

    def test_str_method(self, employer_user, regular_user, course):
        """Тест строкового представления"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        expected = f"{employer_user} -> {regular_user} -> {course.title}"
        assert str(rec) == expected

    def test_is_viewed_update(self, employer_user, regular_user, course):
        """Тест обновления статуса просмотра"""
        rec = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        assert rec.is_viewed is False

        rec.is_viewed = True
        rec.save()
        rec.refresh_from_db()
        assert rec.is_viewed is True

    def test_multiple_employees(
        self, employer_user, regular_user, test_employee_user2, course
    ):
        """Тест рекомендаций нескольким сотрудникам"""
        rec1 = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=regular_user,
            course=course,
        )
        rec2 = EmployerRecommendation.objects.create(
            employer=employer_user,
            employee=test_employee_user2,
            course=course,
        )

        assert EmployerRecommendation.objects.filter(employee=regular_user).count() == 1
        assert (
            EmployerRecommendation.objects.filter(employee=test_employee_user2).count()
            == 1
        )
        assert (
            EmployerRecommendation.objects.filter(employer=employer_user).count() == 2
        )

    def test_multiple_courses_for_employee(
        self, employer_user, regular_user, multiple_courses
    ):
        """Тест нескольких курсов для одного сотрудника"""
        for course in multiple_courses[:3]:
            EmployerRecommendation.objects.create(
                employer=employer_user,
                employee=regular_user,
                course=course,
            )

        assert (
            EmployerRecommendation.objects.filter(
                employer=employer_user, employee=regular_user
            ).count()
            == 3
        )
