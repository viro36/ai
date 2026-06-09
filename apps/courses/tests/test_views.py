import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone
from django.http import HttpResponseForbidden

from apps.courses.models import Course

pytestmark = pytest.mark.django_db


class TestOrganizationAccessMixin:
    """Тесты для миксина проверки доступа"""

    def test_access_granted_for_admin(self, admin_user, course, request_factory):
        """Тест доступа для администратора"""
        from apps.courses.views import OrganizationAccessMixin

        mixin = OrganizationAccessMixin()
        request = request_factory.get("/")
        request.user = admin_user
        mixin.request = request

        # Для ListView
        mixin.kwargs = {"org_id": course.organization.id}
        mixin.get_organization = lambda: course.organization
        assert mixin.test_func() is True

        # Для UpdateView
        mixin.kwargs = {"course_id": course.id}
        mixin.get_object = lambda: course
        assert mixin.test_func() is True

    def test_access_granted_for_university_owner(
        self, authenticated_university_user, course, request_factory
    ):
        """Тест доступа для владельца ВУЗа"""
        from apps.courses.views import OrganizationAccessMixin

        mixin = OrganizationAccessMixin()
        request = request_factory.get("/")
        request.user = authenticated_university_user
        mixin.request = request

        mixin.kwargs = {"org_id": course.organization.id}
        mixin.get_organization = lambda: course.organization
        assert mixin.test_func() is True

    def test_access_denied_for_wrong_university(
        self, authenticated_university_user, another_organization, request_factory
    ):
        """Тест отказа доступа для чужого ВУЗа"""
        from apps.courses.views import OrganizationAccessMixin

        mixin = OrganizationAccessMixin()
        request = request_factory.get("/")
        request.user = authenticated_university_user
        mixin.request = request

        # Пытаемся получить доступ к другой организации
        mixin.kwargs = {"org_id": another_organization.id}
        mixin.get_organization = lambda: another_organization
        assert mixin.test_func() is False

    def test_access_denied_for_regular_user(
        self, regular_user, course, request_factory
    ):
        """Тест отказа доступа для обычного пользователя"""
        from apps.courses.views import OrganizationAccessMixin

        mixin = OrganizationAccessMixin()
        request = request_factory.get("/")
        request.user = regular_user
        mixin.request = request

        mixin.kwargs = {"org_id": course.organization.id}
        mixin.get_organization = lambda: course.organization
        assert mixin.test_func() is False

    def test_handle_no_permission(self, request_factory):
        """Тест обработки отказа в доступе"""
        from apps.courses.views import OrganizationAccessMixin

        mixin = OrganizationAccessMixin()
        request = request_factory.get("/")
        mixin.request = request

        response = mixin.handle_no_permission()
        assert isinstance(response, HttpResponseForbidden)
        assert response.content.decode() == "Доступ запрещён"


class TestOrganizationCoursesListView:
    """Тесты для списка курсов организации"""

    def test_list_view_status_code(
        self, authenticated_university_user, client, organization
    ):
        """Тест статуса 200 для авторизованного пользователя"""
        client.force_login(authenticated_university_user)
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_list_view_requires_login(self, client, organization):
        """Тест требования авторизации"""
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response = client.get(url)
        # Без логина доступ запрещён (403) или редирект на логин (302)
        assert response.status_code in [
            302,
            403,
        ], f"Expected 302 or 403, got {response.status_code}"

        # Если это 403, проверяем сообщение
        if response.status_code == 403:
            assert "Доступ запрещён" in response.content.decode()

    def test_list_view_shows_only_active_courses(
        self,
        authenticated_university_user,
        client,
        organization,
        course,
        deleted_course,
    ):
        """Тест отображения только активных курсов"""
        client.force_login(authenticated_university_user)
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response = client.get(url)

        courses = response.context["courses"]
        assert course in courses
        assert deleted_course not in courses
        assert len(courses) == 1

    def test_list_view_pagination(
        self, authenticated_university_user, client, organization, multiple_courses
    ):
        """Тест пагинации"""
        client.force_login(authenticated_university_user)
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "page_obj" in response.context
        assert len(response.context["courses"]) == 10  # paginate_by=10

    def test_list_view_forbidden_for_regular_user(
        self, regular_user, client, organization
    ):
        """Тест запрета для обычного пользователя"""
        client.force_login(regular_user)
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response = client.get(url)
        assert response.status_code == 403


class TestDeletedCoursesListView:
    """Тесты для списка удалённых курсов"""

    def test_deleted_list_view_shows_only_deleted_courses(
        self,
        authenticated_university_user,
        client,
        organization,
        course,
        deleted_course,
    ):
        """Тест отображения только удалённых курсов"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_deleted_list", kwargs={"org_id": organization.id})
        response = client.get(url)

        courses = response.context["courses"]
        assert deleted_course in courses
        assert course not in courses
        assert len(courses) == 1

    def test_deleted_list_view_ordering(
        self, authenticated_university_user, client, organization
    ):
        """Тест сортировки по дате удаления"""
        client.force_login(authenticated_university_user)

        course1 = Course.objects.create(
            title="Удалённый 1",
            organization=organization,
            url="https://example.com/deleted1",
            is_deleted=True,
            deleted_at=timezone.now(),
        )

        course2 = Course.objects.create(
            title="Удалённый 2",
            organization=organization,
            url="https://example.com/deleted2",
            is_deleted=True,
            deleted_at=timezone.now() - timezone.timedelta(days=1),
        )

        url = reverse("courses:course_deleted_list", kwargs={"org_id": organization.id})
        response = client.get(url)

        courses = response.context["courses"]
        # Должны быть отсортированы по deleted_at DESC
        assert courses[0].deleted_at > courses[1].deleted_at


class TestCourseCreateView:
    """Тесты для создания курса"""

    def test_create_view_get(self, authenticated_university_user, client, organization):
        """Тест GET запроса формы создания"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_add", kwargs={"org_id": organization.id})
        response = client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["is_add"] is True
        assert response.context["organization"] == organization

    def test_create_view_post_valid_data(
        self, authenticated_university_user, client, organization, course_data
    ):
        """Тест POST запроса с валидными данными"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_add", kwargs={"org_id": organization.id})
        response = client.post(url, course_data)

        assert response.status_code == 302  # Redirect
        assert Course.objects.filter(title="Новый тестовый курс").exists()

        course = Course.objects.get(title="Новый тестовый курс")
        assert course.organization == organization
        assert course.url == "https://example.com/course/new"

    def test_create_view_post_invalid_data(
        self, authenticated_university_user, client, organization
    ):
        """Тест POST запроса с невалидными данными"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_add", kwargs={"org_id": organization.id})
        response = client.post(url, {"title": ""})  # Пустое название

        assert response.status_code == 200  # Остаёмся на той же странице
        assert "form" in response.context
        assert response.context["form"].errors

        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Пожалуйста, исправьте ошибки" in str(message) for message in messages
        )

    def test_create_view_success_message(
        self, authenticated_university_user, client, organization, course_data
    ):
        """Тест сообщения об успешном создании"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_add", kwargs={"org_id": organization.id})
        response = client.post(url, course_data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("Курс успешно добавлен" in str(message) for message in messages)


class TestCourseUpdateView:
    """Тесты для редактирования курса"""

    def test_update_view_get(self, authenticated_university_user, client, course):
        """Тест GET запроса формы редактирования"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_edit", kwargs={"course_id": course.id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["course"] == course
        assert response.context["is_add"] is False
        assert response.context["organization"] == course.organization

    def test_update_view_post_valid_data(
        self, authenticated_university_user, client, course, course_update_data
    ):
        """Тест POST запроса с валидными данными"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_edit", kwargs={"course_id": course.id})
        response = client.post(url, course_update_data)

        assert response.status_code == 302
        course.refresh_from_db()
        assert course.title == "Обновлённый курс"
        assert course.description == "Обновлённое описание"
        assert course.duration_hours == 120

    def test_update_view_cannot_edit_deleted_course(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест невозможности редактирования удалённого курса"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_edit", kwargs={"course_id": deleted_course.id})
        response = client.get(url)

        assert response.status_code == 404  # Not found

    def test_update_view_success_message(
        self, authenticated_university_user, client, course, course_update_data
    ):
        """Тест сообщения об успешном обновлении"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_edit", kwargs={"course_id": course.id})
        response = client.post(url, course_update_data, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("Курс успешно обновлён" in str(message) for message in messages)


class TestCourseSoftDeleteView:
    """Тесты для мягкого удаления курса"""

    def test_delete_view_post(self, authenticated_university_user, client, course):
        """Тест POST запроса удаления"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_delete", kwargs={"course_id": course.id})
        response = client.post(url)

        assert response.status_code == 302  # Redirect
        course.refresh_from_db()
        assert course.is_deleted is True
        assert course.deleted_at is not None

    def test_delete_view_get_confirm(
        self, authenticated_university_user, client, course
    ):
        """Тест GET запроса страницы подтверждения"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_delete", kwargs={"course_id": course.id})
        response = client.get(url)

        assert response.status_code == 200
        assert "course" in response.context
        assert response.context["course"] == course
        assert "organization" in response.context

    def test_delete_view_cannot_delete_already_deleted(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест невозможности удаления уже удалённого курса"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_delete", kwargs={"course_id": deleted_course.id})
        response = client.post(url)

        assert response.status_code == 404  # Not found

    def test_delete_view_success_message(
        self, authenticated_university_user, client, course
    ):
        """Тест сообщения об успешном удалении"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_delete", kwargs={"course_id": course.id})
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("перемещён в корзину" in str(message) for message in messages)

    def test_delete_view_redirects_to_courses_list(
        self, authenticated_university_user, client, course
    ):
        """Тест редиректа после удаления"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_delete", kwargs={"course_id": course.id})
        response = client.post(url)

        expected_url = reverse(
            "courses:organization_courses", kwargs={"org_id": course.organization.id}
        )
        assert response.url == expected_url


class TestCourseRestoreView:
    """Тесты для восстановления курса"""

    def test_restore_view_post(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест POST запроса восстановления"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_restore", kwargs={"course_id": deleted_course.id})
        response = client.post(url)

        assert response.status_code == 302
        deleted_course.refresh_from_db()
        assert deleted_course.is_deleted is False
        assert deleted_course.deleted_at is None

    def test_restore_view_get_confirm(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест GET запроса страницы подтверждения восстановления"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_restore", kwargs={"course_id": deleted_course.id})
        response = client.get(url)

        assert response.status_code == 200
        assert "course" in response.context
        assert response.context["course"] == deleted_course
        assert "organization" in response.context

    def test_restore_view_cannot_restore_active_course(
        self, authenticated_university_user, client, course
    ):
        """Тест невозможности восстановления активного курса"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_restore", kwargs={"course_id": course.id})
        response = client.post(url)

        assert response.status_code == 404  # Not found

    def test_restore_view_success_message(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест сообщения об успешном восстановлении"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_restore", kwargs={"course_id": deleted_course.id})
        response = client.post(url, follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("восстановлен" in str(message) for message in messages)

    def test_restore_view_redirects_to_courses_list(
        self, authenticated_university_user, client, deleted_course
    ):
        """Тест редиректа после восстановления"""
        client.force_login(authenticated_university_user)
        url = reverse("courses:course_restore", kwargs={"course_id": deleted_course.id})
        response = client.post(url)

        expected_url = reverse(
            "courses:organization_courses",
            kwargs={"org_id": deleted_course.organization.id},
        )
        assert response.url == expected_url


class TestViewPermissions:
    """Тесты прав доступа для всех вьюх"""

    def test_all_views_require_login(
        self, client, organization, course, deleted_course
    ):
        """Тест требования авторизации для всех вьюх"""
        urls = [
            reverse("courses:organization_courses", kwargs={"org_id": organization.id}),
            reverse("courses:course_deleted_list", kwargs={"org_id": organization.id}),
            reverse("courses:course_add", kwargs={"org_id": organization.id}),
            reverse("courses:course_edit", kwargs={"course_id": course.id}),
            reverse("courses:course_delete", kwargs={"course_id": course.id}),
            reverse("courses:course_restore", kwargs={"course_id": deleted_course.id}),
        ]

        for url in urls:
            response = client.get(url)
            # Без логина должно быть либо 302 (редирект на логин) либо 403 (доступ запрещён)
            assert response.status_code in [
                302,
                403,
            ], f"Failed for {url}. Got {response.status_code}"

    def test_university_cannot_access_other_organization(
        self, authenticated_university_user, client, another_organization
    ):
        """Тест невозможности доступа к курсам другой организации"""
        client.force_login(authenticated_university_user)

        # Пытаемся получить курсы другой организации
        url = reverse(
            "courses:organization_courses", kwargs={"org_id": another_organization.id}
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_regular_user_cannot_access_any_course_views(
        self, regular_user, client, organization, course
    ):
        """Тест полного запрета доступа для обычного пользователя"""
        client.force_login(regular_user)

        urls = [
            reverse("courses:organization_courses", kwargs={"org_id": organization.id}),
            reverse("courses:course_edit", kwargs={"course_id": course.id}),
            reverse("courses:course_delete", kwargs={"course_id": course.id}),
        ]

        for url in urls:
            response = client.get(url)
            assert response.status_code == 403, f"Should be forbidden for {url}"

    def test_admin_can_access_all_organizations(
        self, admin_user, client, organization, another_organization, course
    ):
        """Тест полного доступа для администратора"""
        client.force_login(admin_user)

        # Доступ к первой организации
        url1 = reverse(
            "courses:organization_courses", kwargs={"org_id": organization.id}
        )
        response1 = client.get(url1)
        assert response1.status_code == 200

        # Доступ ко второй организации
        url2 = reverse(
            "courses:organization_courses", kwargs={"org_id": another_organization.id}
        )
        response2 = client.get(url2)
        assert response2.status_code == 200

        # Редактирование курса
        url3 = reverse("courses:course_edit", kwargs={"course_id": course.id})
        response3 = client.get(url3)
        assert response3.status_code == 200
