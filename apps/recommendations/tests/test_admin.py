import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.utils import timezone

from apps.recommendations.admin import (
    ApprovedSelectedCourseAdmin,
    CourseRecommendationAdmin,
    EmployerRecommendationAdmin,
    RecommendationTaskAdmin,
    SelectedCourseAdmin,
)
from apps.recommendations.admin_filters import (
    ApprovalStatusFilter,
    ApprovedByFilter,
    ApprovedEmploymentFilter,
    SelectedEmploymentFilter,
)
from apps.recommendations.models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
    RecommendationTask,
    SelectedCourse,
)

pytestmark = pytest.mark.django_db


# ============================================================
# CourseRecommendation
# ============================================================
class TestCourseRecommendationAdmin:
    """Тесты для админки CourseRecommendation."""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = CourseRecommendationAdmin(CourseRecommendation, self.admin_site)

    def test_list_display(self):
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
        assert "is_viewed" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter

    def test_search_fields(self):
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_list_editable(self):
        assert "order" in self.admin.list_editable
        assert "is_viewed" in self.admin.list_editable

    def test_readonly_fields(self):
        assert "created_at" in self.admin.readonly_fields
        assert "relevance_score" in self.admin.readonly_fields

    def test_relevance_score_display(self, course_recommendation):
        result = self.admin.relevance_score_display(course_recommendation)
        assert result == "85%"

    def test_has_add_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_change_permission(request) is False

    def test_has_delete_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_delete_permission(request) is False


# ============================================================
# RecommendationTask
# ============================================================
class TestRecommendationTaskAdmin:
    """Тесты для админки RecommendationTask."""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = RecommendationTaskAdmin(RecommendationTask, self.admin_site)

    def test_list_display(self):
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
        assert "status" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter

    def test_search_fields(self):
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "task_id" in self.admin.search_fields

    def test_list_editable(self):
        assert "status" in self.admin.list_editable

    def test_readonly_fields(self):
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields
        assert "task_id" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False


# ============================================================
# SelectedCourse
# ============================================================
class TestSelectedCourseAdmin:
    """Тесты для админки SelectedCourse."""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = SelectedCourseAdmin(SelectedCourse, self.admin_site)

    def test_list_display(self):
        expected = (
            "id",
            "employee_name",
            "course_title",
            "employment_status_display",
            "approval_status_display",
            "created_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter_contains_custom_and_standard(self):
        lf = self.admin.list_filter
        assert ApprovalStatusFilter in lf
        assert SelectedEmploymentFilter in lf
        assert ApprovedByFilter in lf
        assert "created_at" in lf

    def test_search_fields(self):
        assert "user__username" in self.admin.search_fields
        assert "user__email" in self.admin.search_fields
        assert "user__patronymic" in self.admin.search_fields
        assert "user__organization__short_name" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_readonly_fields(self):
        assert "created_at" in self.admin.readonly_fields

    def test_list_select_related(self):
        assert "user" in self.admin.list_select_related
        assert "user__employee_profile" in self.admin.list_select_related
        assert "course" in self.admin.list_select_related
        assert "approval" in self.admin.list_select_related

    def test_actions_registered(self):
        assert "approve_selected" in self.admin.actions
        assert "reject_selected" in self.admin.actions

    # ---------- Методы отображения ----------
    def test_employee_name_contains_full_name(self, selected_course):
        html = self.admin.employee_name(selected_course)
        user = selected_course.user
        assert user.last_name in html
        assert user.first_name in html

    def test_employee_name_has_link(self, selected_course):
        html = self.admin.employee_name(selected_course)
        expected_url = reverse(
            "admin:users_customuser_change", args=[selected_course.user.pk]
        )
        assert expected_url in html

    def test_course_title_has_link(self, selected_course):
        html = self.admin.course_title(selected_course)
        expected_url = reverse(
            "admin:courses_course_change", args=[selected_course.course.pk]
        )
        assert expected_url in html
        assert selected_course.course.title in html

    def test_employment_status_unemployed(self, selected_course_unemployed):
        html = self.admin.employment_status_display(selected_course_unemployed)
        assert "Безработный" in html

    def test_employment_status_svo(self, selected_course_svo):
        html = self.admin.employment_status_display(selected_course_svo)
        assert "Участник СВО" in html

    def test_employment_status_organization(self, selected_course):
        html = self.admin.employment_status_display(selected_course)
        profile = selected_course.user.employee_profile
        assert profile.organization.short_name in html

    def test_approval_status_not_reviewed(self, selected_course):
        html = self.admin.approval_status_display(selected_course)
        assert "не рассмотрено" in html

    def test_approval_status_approved(self, selected_course):
        ApprovedSelectedCourse.objects.create(
            selected_course=selected_course,
            status="approved",
            approved_at=timezone.now(),
        )
        selected_course.refresh_from_db()
        html = self.admin.approval_status_display(selected_course)
        assert "Одобрено" in html

    # ---------- Actions ----------
    def test_approve_selected_creates_approval(self, admin_request, selected_course):
        self.admin.approve_selected(
            admin_request,
            SelectedCourse.objects.filter(pk=selected_course.pk),
        )
        approval = ApprovedSelectedCourse.objects.get(selected_course=selected_course)
        assert approval.status == "approved"
        assert approval.approved_by == admin_request.user
        assert approval.approved_at is not None

    def test_reject_selected_creates_approval(self, admin_request, selected_course):
        self.admin.reject_selected(
            admin_request,
            SelectedCourse.objects.filter(pk=selected_course.pk),
        )
        approval = ApprovedSelectedCourse.objects.get(selected_course=selected_course)
        assert approval.status == "rejected"
        assert approval.approved_by == admin_request.user

    def test_approve_selected_updates_existing(self, admin_request, selected_course):
        ApprovedSelectedCourse.objects.create(
            selected_course=selected_course,
            status="pending",
        )
        self.admin.approve_selected(
            admin_request,
            SelectedCourse.objects.filter(pk=selected_course.pk),
        )
        approval = ApprovedSelectedCourse.objects.get(selected_course=selected_course)
        assert approval.status == "approved"
        assert approval.approved_by == admin_request.user

    # ---------- Права ----------
    def test_has_add_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False


# ============================================================
# ApprovedSelectedCourse
# ============================================================
class TestApprovedSelectedCourseAdmin:
    """Тесты для админки ApprovedSelectedCourse."""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = ApprovedSelectedCourseAdmin(
            ApprovedSelectedCourse, self.admin_site
        )

    def test_list_display(self):
        expected = (
            "id",
            "employee_name",
            "course_title",
            "employment_status_display",
            "status",
            "approved_by_display",
            "approved_at",
        )
        assert self.admin.list_display == expected

    def test_list_filter(self):
        assert "status" in self.admin.list_filter
        assert "approved_at" in self.admin.list_filter
        assert ApprovedEmploymentFilter in self.admin.list_filter

    def test_search_fields(self):
        assert "selected_course__user__username" in self.admin.search_fields
        assert "selected_course__user__patronymic" in self.admin.search_fields
        assert "selected_course__course__title" in self.admin.search_fields

    def test_readonly_fields(self):
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields

    def test_list_editable(self):
        assert "status" in self.admin.list_editable

    # ---------- Методы отображения ----------
    def test_employee_name(self, approved_course):
        html = self.admin.employee_name(approved_course)
        user = approved_course.selected_course.user
        assert user.last_name in html
        expected_url = reverse("admin:users_customuser_change", args=[user.pk])
        assert expected_url in html

    def test_course_title(self, approved_course):
        html = self.admin.course_title(approved_course)
        course = approved_course.selected_course.course
        assert course.title in html
        expected_url = reverse("admin:courses_course_change", args=[course.pk])
        assert expected_url in html

    def test_approved_by_display_none(self, approved_course):
        approved_course.approved_by = None
        assert self.admin.approved_by_display(approved_course) == "—"

    def test_approved_by_display_with_user(self, approved_course, admin_user):
        approved_course.approved_by = admin_user
        html = self.admin.approved_by_display(approved_course)
        name = admin_user.get_full_name() or admin_user.username
        assert name in html
        expected_url = reverse("admin:users_customuser_change", args=[admin_user.pk])
        assert expected_url in html

    def test_employment_status_display(self, approved_course):
        html = self.admin.employment_status_display(approved_course)
        profile = approved_course.selected_course.user.employee_profile
        assert profile.organization.short_name in html

    # ---------- Права ----------
    def test_has_add_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False

    def test_has_change_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_change_permission(request) is False

    def test_has_delete_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_delete_permission(request) is False


# ============================================================
# EmployerRecommendation
# ============================================================
class TestEmployerRecommendationAdmin:
    """Тесты для админки EmployerRecommendation."""

    def setup_method(self):
        self.admin_site = AdminSite()
        self.admin = EmployerRecommendationAdmin(
            EmployerRecommendation, self.admin_site
        )

    def test_list_display(self):
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
        assert "is_viewed" in self.admin.list_filter
        assert "created_at" in self.admin.list_filter
        assert "updated_at" in self.admin.list_filter

    def test_search_fields(self):
        assert "employer__username" in self.admin.search_fields
        assert "employer__email" in self.admin.search_fields
        assert "employee__username" in self.admin.search_fields
        assert "course__title" in self.admin.search_fields

    def test_list_editable(self):
        assert "is_viewed" in self.admin.list_editable

    def test_readonly_fields(self):
        assert "created_at" in self.admin.readonly_fields
        assert "updated_at" in self.admin.readonly_fields

    def test_has_add_permission_for_viewer(self, viewer_user):
        request = type("Request", (), {"user": viewer_user})()
        assert self.admin.has_add_permission(request) is False


# ============================================================
# Кастомные фильтры
# ============================================================
class TestApprovalStatusFilter:
    def test_lookups(self):
        f = ApprovalStatusFilter(
            None, {}, SelectedCourse, SelectedCourseAdmin(SelectedCourse, AdminSite())
        )
        values = [v for v, _ in f.lookups(None, None)]
        assert values == ["none", "pending", "approved", "rejected"]


class TestSelectedEmploymentFilter:
    def test_lookups(self):
        f = SelectedEmploymentFilter(
            None, {}, SelectedCourse, SelectedCourseAdmin(SelectedCourse, AdminSite())
        )
        values = [v for v, _ in f.lookups(None, None)]
        assert values == ["unemployed", "svo", "employed"]


class TestApprovedEmploymentFilter:
    def test_lookups(self):
        f = ApprovedEmploymentFilter(
            None,
            {},
            ApprovedSelectedCourse,
            ApprovedSelectedCourseAdmin(ApprovedSelectedCourse, AdminSite()),
        )
        values = [v for v, _ in f.lookups(None, None)]
        assert values == ["unemployed", "svo", "employed"]


# ============================================================
# Права просмотрщика через реальный client
# ============================================================
class TestViewerPermissions:
    """Тесты для проверки прав просмотрщика через реальный client."""

    def test_viewer_can_view_recommendations(self, viewer_client):
        url = reverse("admin:recommendations_courserecommendation_changelist")
        assert viewer_client.get(url).status_code == 200

    def test_viewer_can_view_tasks(self, viewer_client):
        url = reverse("admin:recommendations_recommendationtask_changelist")
        assert viewer_client.get(url).status_code == 200

    def test_viewer_can_view_selected_courses(self, viewer_client):
        url = reverse("admin:recommendations_selectedcourse_changelist")
        assert viewer_client.get(url).status_code == 200

    def test_viewer_can_view_approved_courses(self, viewer_client):
        url = reverse("admin:recommendations_approvedselectedcourse_changelist")
        assert viewer_client.get(url).status_code == 200

    def test_viewer_can_view_employer_recommendations(self, viewer_client):
        url = reverse("admin:recommendations_employerrecommendation_changelist")
        assert viewer_client.get(url).status_code == 200

    def test_viewer_cannot_add_recommendation(self, viewer_client):
        url = reverse("admin:recommendations_courserecommendation_add")
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_add_task(self, viewer_client):
        url = reverse("admin:recommendations_recommendationtask_add")
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_add_selected_course(self, viewer_client):
        url = reverse("admin:recommendations_selectedcourse_add")
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_add_approved_course(self, viewer_client):
        url = reverse("admin:recommendations_approvedselectedcourse_add")
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_add_employer_recommendation(self, viewer_client):
        url = reverse("admin:recommendations_employerrecommendation_add")
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_delete_recommendation(
        self, viewer_client, course_recommendation
    ):
        url = reverse(
            "admin:recommendations_courserecommendation_delete",
            args=[course_recommendation.id],
        )
        assert viewer_client.get(url).status_code in (302, 403)

    def test_viewer_cannot_edit_recommendation(
        self, viewer_client, course_recommendation
    ):
        url = reverse(
            "admin:recommendations_courserecommendation_change",
            args=[course_recommendation.id],
        )
        response = viewer_client.post(url, {"order": 10, "is_viewed": True})
        assert response.status_code in (302, 403)

    def test_viewer_has_no_action_form_in_changelist(self, viewer_client):
        """У просмотрщика нет формы массовых действий (action_form = None)."""
        url = reverse("admin:recommendations_selectedcourse_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200
        assert response.context.get("action_form") is None

    def test_admin_has_action_form_in_changelist(self, admin_client):
        """У админа есть action_form в changelist."""
        url = reverse("admin:recommendations_selectedcourse_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert response.context.get("action_form") is not None
