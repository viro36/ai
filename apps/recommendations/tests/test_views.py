import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from datetime import datetime

from apps.recommendations.models import (
    CourseRecommendation,
    RecommendationTask,
    SelectedCourse,
)
from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course
from apps.goal_setting.models import Question, GoalSettingResponse

pytestmark = pytest.mark.django_db

User = get_user_model()


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

    def test_view_selected_course_ids(self, client, regular_user, course):
        """Тест передачи ID выбранных курсов в контекст"""
        # Создаём выбранный курс
        SelectedCourse.objects.create(user=regular_user, course=course)

        # Создаём рекомендацию
        CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
        )

        client.force_login(regular_user)
        url = reverse("recommendations:my_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert course.id in response.context["selected_course_ids"]


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


class TestCheckRecommendationsStatusView:
    """Тесты для проверки статуса генерации"""

    def test_status_requires_login(self, client):
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_status_pending(self, client, regular_user, recommendation_task):
        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_status_completed(self, client, regular_user, organization):
        """Тест статуса completed"""
        # Создаём завершённую задачу
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="completed",
        )
        # Создаём курс с организацией
        course = Course.objects.create(
            title="Курс",
            organization=organization,
            url="https://test.com",
            is_deleted=False,
        )
        # Создаём рекомендацию
        CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason="Тест",
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
        task = RecommendationTask.objects.create(
            user=regular_user,
            task_id="task-123",
            status="failed",
            error_message="Ошибка генерации",
        )

        client.force_login(regular_user)
        url = reverse("recommendations:check_status")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Ошибка генерации"


class TestSelectCourseView:
    """Тесты для выбора курса"""

    def test_select_requires_login(self, client, course):
        url = reverse("recommendations:select_course", args=[course.id])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_select_course_success(self, client, regular_user, course):
        client.force_login(regular_user)
        url = reverse("recommendations:select_course", args=[course.id])
        response = client.post(url, follow=True)

        assert response.status_code == 200
        assert SelectedCourse.objects.filter(user=regular_user, course=course).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any("успешно выбран" in str(msg).lower() for msg in messages)

    def test_select_course_already_selected(self, client, regular_user, course):
        SelectedCourse.objects.create(user=regular_user, course=course)

        client.force_login(regular_user)
        url = reverse("recommendations:select_course", args=[course.id])
        response = client.post(url, follow=True)

        assert response.status_code == 200
        # Проверяем, что дубликат не создался
        assert (
            SelectedCourse.objects.filter(user=regular_user, course=course).count() == 1
        )

        messages = list(get_messages(response.wsgi_request))
        assert any("уже был выбран" in str(msg).lower() for msg in messages)

    def test_select_deleted_course(self, client, regular_user, deleted_course):
        client.force_login(regular_user)
        url = reverse("recommendations:select_course", args=[deleted_course.id])
        response = client.post(url)
        assert response.status_code == 404


class TestSelectedCoursesView:
    """Тесты для списка выбранных курсов"""

    def test_selected_requires_login(self, client):
        url = reverse("recommendations:selected_courses")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_selected_empty(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:selected_courses")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["total"] == 0
        assert len(response.context["selected_courses"]) == 0

    def test_selected_with_courses(self, client, regular_user, multiple_courses):
        for course in multiple_courses[:3]:
            SelectedCourse.objects.create(user=regular_user, course=course)

        client.force_login(regular_user)
        url = reverse("recommendations:selected_courses")
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["total"] == 3
        assert len(response.context["selected_courses"]) == 3


class TestRemoveSelectedCourseView:
    """Тесты для удаления выбранного курса"""

    def test_remove_requires_login(self, client, course):
        url = reverse("recommendations:remove_selected_course", args=[course.id])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_remove_success(self, client, regular_user, course):
        SelectedCourse.objects.create(user=regular_user, course=course)

        client.force_login(regular_user)
        url = reverse("recommendations:remove_selected_course", args=[course.id])
        response = client.post(url, follow=True)

        assert response.status_code == 200
        assert not SelectedCourse.objects.filter(
            user=regular_user, course=course
        ).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any("удалён из выбранных" in str(msg).lower() for msg in messages)

    def test_remove_nonexistent(self, client, regular_user, course):
        client.force_login(regular_user)
        url = reverse("recommendations:remove_selected_course", args=[course.id])
        response = client.post(url, follow=True)

        assert response.status_code == 200
        # Просто проверяем, что ошибки нет
        assert "Курс" in str(list(get_messages(response.wsgi_request))[0])


class TestEmployerRecommendationsView:
    """Тесты для страницы рекомендаций курсов работодателем"""

    def test_employer_recommendations_requires_login(self, client):
        url = reverse("recommendations:employer_recommendations")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_employer_recommendations_requires_employer(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:employer_recommendations")
        response = client.get(url)
        assert response.status_code == 302

    def test_employer_recommendations_returns_200_for_employer(
        self, client, test_employer_user
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:employer_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert "categories" in response.context
        assert "positions" in response.context
        assert "employees" in response.context

    def test_employer_recommendations_search_by_name(
        self, client, test_employer_user, test_employee_user
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:employer_recommendations")
        response = client.get(url, {"search": "Иван"})
        assert response.status_code == 200
        employees = response.context["employees"]
        assert test_employee_user in employees

    def test_employer_recommendations_search_by_position(
        self, client, test_employer_user, test_employee_user
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:employer_recommendations")
        response = client.get(url, {"search": "Начальник"})
        assert response.status_code == 200
        employees = response.context["employees"]
        assert test_employee_user in employees


class TestGetEmployeesByPositionView:
    """Тесты для AJAX получения работников по должности"""

    def test_get_employees_by_position_requires_login(self, client):
        url = reverse("recommendations:get_employees_by_position")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_employees_by_position_requires_employer(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:get_employees_by_position")
        response = client.get(url)
        assert response.status_code == 403

    def test_get_employees_by_position_success(
        self, client, test_employer_user, test_employee_user
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:get_employees_by_position")
        response = client.get(url, {"position": "Начальник цеха"})
        assert response.status_code == 200
        data = response.json()
        assert "employees" in data
        assert len(data["employees"]) == 1
        assert data["employees"][0]["id"] == test_employee_user.id

    def test_get_employees_by_position_empty(self, client, test_employer_user):
        client.force_login(test_employer_user)
        url = reverse("recommendations:get_employees_by_position")
        response = client.get(url, {"position": "Несуществующая должность"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["employees"]) == 0


class TestGetCoursesByCategoryView:
    """Тесты для AJAX получения курсов по категории"""

    def test_get_courses_by_category_requires_login(self, client):
        url = reverse("recommendations:get_courses_by_category")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_get_courses_by_category_requires_employer(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:get_courses_by_category")
        response = client.get(url)
        assert response.status_code == 403

    def test_get_courses_by_category_success(
        self, client, test_employer_user, course, category
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:get_courses_by_category")
        response = client.get(url, {"category_id": category.id})
        assert response.status_code == 200
        data = response.json()
        assert "courses" in data
        assert len(data["courses"]) == 1
        assert data["courses"][0]["title"] == course.title

    def test_get_courses_by_category_empty(self, client, test_employer_user):
        client.force_login(test_employer_user)
        url = reverse("recommendations:get_courses_by_category")
        response = client.get(url, {"category_id": 999})
        assert response.status_code == 200
        data = response.json()
        assert len(data["courses"]) == 0


class TestSendEmployerRecommendationView:
    """Тесты для отправки рекомендации работодателем"""

    def test_send_recommendation_requires_login(self, client):
        url = reverse("recommendations:send_employer_recommendation")
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_send_recommendation_requires_employer(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("recommendations:send_employer_recommendation")
        response = client.post(url, {})
        assert response.status_code == 302

    def test_send_recommendation_success(
        self, client, test_employer_user, test_employee_user, course
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:send_employer_recommendation")
        data = {
            "employee_id": test_employee_user.id,
            "course_id": course.id,
            "reason": "Хороший курс для развития",
        }
        response = client.post(url, data, follow=True)
        assert response.status_code == 200

        from apps.recommendations.models import EmployerRecommendation

        assert EmployerRecommendation.objects.filter(
            employer=test_employer_user,
            employee=test_employee_user,
            course=course,
        ).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any("рекомендован" in str(msg).lower() for msg in messages)

    def test_send_recommendation_wrong_employee(
        self, client, test_employer_user, another_organization, course
    ):
        # Создаём сотрудника в другой организации
        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="pass123",
            user_type="employee",
            organization=another_organization,
        )

        client.force_login(test_employer_user)
        url = reverse("recommendations:send_employer_recommendation")
        data = {
            "employee_id": other_employee.id,
            "course_id": course.id,
        }
        response = client.post(url, data, follow=True)
        messages = list(get_messages(response.wsgi_request))
        assert any("не принадлежит" in str(msg).lower() for msg in messages)


class TestEmployeeEmployerRecommendationsView:
    """Тесты для просмотра рекомендаций от работодателя работником"""

    def test_employee_employer_recommendations_requires_login(self, client):
        url = reverse("recommendations:employee_employer_recommendations")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_employee_employer_recommendations_requires_employee(
        self, client, test_employer_user
    ):
        client.force_login(test_employer_user)
        url = reverse("recommendations:employee_employer_recommendations")
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_employer_recommendations_returns_200(
        self, client, test_employee_user, employer_recommendation
    ):
        client.force_login(test_employee_user)
        url = reverse("recommendations:employee_employer_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        assert "recommendations" in response.context
        assert "total" in response.context
        assert "selected_course_ids" in response.context

    def test_employee_employer_recommendations_marks_viewed(
        self, client, test_employee_user, employer_recommendation
    ):
        client.force_login(test_employee_user)
        url = reverse("recommendations:employee_employer_recommendations")
        response = client.get(url)
        assert response.status_code == 200
        employer_recommendation.refresh_from_db()
        assert employer_recommendation.is_viewed is True


class TestRemoveEmployerRecommendationView:
    """Тесты для удаления рекомендации работодателем"""

    def test_remove_recommendation_requires_login(self, client):
        url = reverse("recommendations:remove_employer_recommendation", args=[1])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_remove_recommendation_success(
        self, client, test_employer_user, employer_recommendation
    ):
        client.force_login(test_employer_user)
        url = reverse(
            "recommendations:remove_employer_recommendation",
            args=[employer_recommendation.id],
        )
        response = client.post(url, follow=True)
        assert response.status_code == 200

        from apps.recommendations.models import EmployerRecommendation

        assert not EmployerRecommendation.objects.filter(
            id=employer_recommendation.id
        ).exists()

        messages = list(get_messages(response.wsgi_request))
        assert any("удалена" in str(msg).lower() for msg in messages)


class TestEmployeeRecommendationsDetailView:
    """Тесты для детального просмотра рекомендаций сотрудника"""

    def test_employee_recommendations_detail_requires_login(self, client):
        url = reverse("recommendations:employee_recommendations_detail", args=[1])
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_employee_recommendations_detail_requires_employer(
        self, client, regular_user, test_employee_user
    ):
        client.force_login(regular_user)
        url = reverse(
            "recommendations:employee_recommendations_detail",
            args=[test_employee_user.id],
        )
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_recommendations_detail_returns_200(
        self, client, test_employer_user, test_employee_user, employer_recommendation
    ):
        client.force_login(test_employer_user)
        url = reverse(
            "recommendations:employee_recommendations_detail",
            args=[test_employee_user.id],
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "employee" in response.context
        assert "recommendations" in response.context
        assert "total" in response.context
        assert response.context["employee"] == test_employee_user

    def test_employee_recommendations_detail_404_for_wrong_employee(
        self, client, test_employer_user, another_organization
    ):
        # Создаём сотрудника в другой организации
        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="pass123",
            user_type="employee",
            organization=another_organization,
        )

        client.force_login(test_employer_user)
        url = reverse(
            "recommendations:employee_recommendations_detail", args=[other_employee.id]
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_employee_recommendations_detail_shows_only_own_recommendations(
        self, client, test_employer_user, test_employee_user, employer_recommendation
    ):
        # Создаём другого работодателя
        other_employer = User.objects.create_user(
            username="other_employer",
            email="other_emp@test.com",
            password="pass123",
            user_type="employer",
            organization=test_employer_user.organization,
        )

        # Создаём рекомендацию от другого работодателя
        from apps.recommendations.models import EmployerRecommendation

        EmployerRecommendation.objects.create(
            employer=other_employer,
            employee=test_employee_user,
            course=employer_recommendation.course,
        )

        client.force_login(test_employer_user)
        url = reverse(
            "recommendations:employee_recommendations_detail",
            args=[test_employee_user.id],
        )
        response = client.get(url)
        assert response.status_code == 200
        # Должна быть только одна рекомендация (от test_employer_user)
        assert response.context["total"] == 1
