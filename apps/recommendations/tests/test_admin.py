import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.recommendations.admin import (
    ApprovedSelectedCourseAdmin,
    CourseRecommendationAdmin,
    EmployerRecommendationAdmin,
    RecommendationTaskAdmin,
    SelectedCourseAdmin,
)
from apps.recommendations.models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
    RecommendationTask,
    SelectedCourse,
)

pytestmark = pytest.mark.django_db


class TestCourseRecommendationAdmin:
    """Тесты для админки CourseRecommendation"""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = CourseRecommendationAdmin(CourseRecommendation, self.admin_site)

    def test_list_display(self):
        """Тест отображаемых полей"""
        expected = (
            "id",
            "user",
            "course",
            "relevance_score_display",
            "order",
            "is_viewed",
            "created_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Тест фильтров"""
        assert "is_viewed" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_list_editable(self):
        """Тест редактируемых полей в списке"""
        assert "order" in self.admin.list_editable
        assert "is_viewed" in self.admin.list_editable

    def test_relevance_score_display(self, course_recommendation):
        """Тест отображения релевантности в процентах"""
        result = self.admin.relevance_score_display(course_recommendation)
        assert result == "85%"

    def test_readonly_fields(self):
        """Тест readonly полей"""
        assert "created_at" in self.admin.readonly_fields
        assert "relevance_score" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может добавлять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может изменять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_change_permission(request) is False

    def test_has_delete_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может удалять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_delete_permission(request) is False


class TestRecommendationTaskAdmin:
    """Тесты для админки RecommendationTask"""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = RecommendationTaskAdmin(RecommendationTask, self.admin_site)

    def test_list_display(self):
        """Тест отображаемых полей"""
        expected = (
            "id",
            "user",
            "status",
            "task_id",
            "created_at",
            "updated_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Тест фильтров"""
        assert "status" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "task_id" in self.admin.search_fields

    def test_list_editable(self):
        """Тест редактируемых полей в списке"""
        assert "status" in self.admin.list_editable

    def test_readonly_fields(self):
        """Тест readonly полей"""
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields
        assert "task_id" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может добавлять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False


class TestSelectedCourseAdmin:
    """Тесты для админки SelectedCourse"""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = SelectedCourseAdmin(SelectedCourse, self.admin_site)

    def test_list_display(self):
        """Тест отображаемых полей"""
        expected = (
            "id",
            "user",
            "course",
            "created_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Тест фильтров"""
        assert "created_at" in self.admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_readonly_fields(self):
        """Тест readonly полей"""
        assert "created_at" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может добавлять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False


class TestEmployerRecommendationAdmin:
    """Тесты для админки EmployerRecommendation"""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = EmployerRecommendationAdmin(
            EmployerRecommendation, self.admin_site
        )

    def test_list_display(self):
        """Тест отображаемых полей"""
        expected = (
            "id",
            "employer",
            "employee",
            "course",
            "is_viewed",
            "created_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Тест фильтров"""
        assert "is_viewed" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter
        assert "updated_at" in self.admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        assert "employer__username" in self.admin.search_fields
        assert "employer__email" in self.admin.search_fields
        assert "employee__username" in self.admin.search_fields
        assert "employee__email" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_list_editable(self):
        """Тест редактируемых полей в списке"""
        assert "is_viewed" in self.admin.list_editable

    def test_readonly_fields(self):
        """Тест readonly полей"""
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может добавлять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может изменять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_change_permission(request) is False

    def test_has_delete_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может удалять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_delete_permission(request) is False


class TestApprovedSelectedCourseAdmin:
    """Тесты для админки ApprovedSelectedCourse"""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = ApprovedSelectedCourseAdmin(
            ApprovedSelectedCourse, self.admin_site
        )

    def test_list_display(self):
        """Тест отображаемых полей"""
        expected = ("selected_course", "status", "approved_by", "approved_at")
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Тест фильтров"""
        assert "status" in self.admin.list_filter
        assert "approved_at" in self.admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        assert "selected_course__user__username" in self.admin.search_fields
        assert "selected_course__course__title" in self.admin.search_fields

    def test_readonly_fields(self):
        """Тест readonly полей"""
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields

    def test_list_editable(self):
        """Тест редактируемых полей в списке"""
        assert "status" in self.admin.list_editable

    def test_has_add_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может добавлять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может изменять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_change_permission(request) is False

    def test_has_delete_permission_for_viewer(self, viewer_user):
        """Тест - просмотрщик не может удалять"""
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_delete_permission(request) is False


class TestViewerPermissions:
    """Тесты для проверки прав просмотрщика в админке рекомендаций"""

    def test_viewer_can_view_recommendations(self, viewer_client):
        """Тест - просмотрщик может видеть список рекомендаций"""
        url = reverse("admin:recommendations_courserecommendation_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_can_view_tasks(self, viewer_client):
        """Тест - просмотрщик может видеть список задач"""
        url = reverse("admin:recommendations_recommendationtask_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_can_view_selected_courses(self, viewer_client):
        """Тест - просмотрщик может видеть список выбранных курсов"""
        url = reverse("admin:recommendations_selectedcourse_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_cannot_add_recommendation(self, viewer_client):
        """Тест - просмотрщик не может добавлять рекомендации"""
        url = reverse("admin:recommendations_courserecommendation_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_add_task(self, viewer_client):
        """Тест - просмотрщик не может добавлять задачи"""
        url = reverse("admin:recommendations_recommendationtask_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_add_selected_course(self, viewer_client):
        """Тест - просмотрщик не может добавлять выбранные курсы"""
        url = reverse("admin:recommendations_selectedcourse_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_edit_recommendation(
        self, viewer_client, course_recommendation
    ):
        """Тест - просмотрщик не может редактировать рекомендации"""
        url = reverse(
            "admin:recommendations_courserecommendation_change",
            args=[course_recommendation.id],
        )
        # Пытаемся отправить POST запрос на изменение
        data = {
            "order": 10,
            "is_viewed": True,
        }
        response = viewer_client.post(url, data)
        # Должен быть редирект или 403
        assert response.status_code in [302, 403]

    def test_viewer_cannot_delete_recommendation(
        self, viewer_client, course_recommendation
    ):
        """Тест - просмотрщик не может удалять рекомендации"""
        url = reverse(
            "admin:recommendations_courserecommendation_delete",
            args=[course_recommendation.id],
        )
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_has_no_actions_on_recommendations(self, viewer_client):
        """Тест - у просмотрщика нет выпадающего списка действий в рекомендациях"""
        url = reverse("admin:recommendations_courserecommendation_changelist")
        response = viewer_client.get(url)
        content = response.content.decode()
        assert 'name="action"' not in content or "action" not in content.lower()

    def test_admin_has_actions_on_recommendations(self, admin_client):
        """Тест - у администратора есть выпадающий список действий в рекомендациях"""
        url = reverse("admin:recommendations_courserecommendation_changelist")
        response = admin_client.get(url)
        content = response.content.decode()
        assert "Действия" in content or "action" in content.lower()

    def test_viewer_can_view_employer_recommendations(self, viewer_client):
        """Тест - просмотрщик может видеть список рекомендаций от работодателя"""
        url = reverse("admin:recommendations_employerrecommendation_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_can_view_approved_courses(self, viewer_client):
        """Тест - просмотрщик может видеть список одобренных курсов"""
        url = reverse("admin:recommendations_approvedselectedcourse_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_cannot_add_employer_recommendation(self, viewer_client):
        """Тест - просмотрщик не может добавлять рекомендации от работодателя"""
        url = reverse("admin:recommendations_employerrecommendation_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_add_approved_course(self, viewer_client):
        """Тест - просмотрщик не может добавлять одобренные курсы"""
        url = reverse("admin:recommendations_approvedselectedcourse_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]
