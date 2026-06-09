import pytest
from unittest.mock import patch
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponseRedirect

from apps.courses.admin import (
    CourseAdmin,
    CategoryAdmin,
    CourseResource,
    SoftDeleteFilter,
)
from apps.courses.models import Course, Category

User = get_user_model()


pytestmark = pytest.mark.django_db


class MockRequest:
    """Мок запроса для тестирования админки"""

    def __init__(self, user=None):
        self.user = user
        self.session = {}
        self._messages = FallbackStorage(self)
        self.META = {"HTTP_REFERER": "/admin/"}
        self.POST = {}
        self.GET = {}

    def get_full_path(self):
        return "/admin/"


class TestCourseResource:
    """Тесты для ресурса экспорта/импорта курсов"""

    def test_resource_meta_fields(self):
        """Тест мета-полей ресурса"""
        resource = CourseResource()
        assert resource._meta.model == Course
        assert "id" in resource._meta.fields
        assert "title" in resource._meta.fields
        assert "organization__short_name" in resource._meta.fields
        assert "organization__inn" in resource._meta.fields
        assert "is_deleted" in resource._meta.fields
        assert "deleted_at" in resource._meta.fields

    def test_dehydrate_organization_short_name(self, course):
        """Тест получения короткого названия организации"""
        resource = CourseResource()
        result = resource.dehydrate_organization__short_name(course)
        assert result == course.organization.short_name

    def test_dehydrate_organization_inn(self, course):
        """Тест получения ИНН организации"""
        resource = CourseResource()
        result = resource.dehydrate_organization__inn(course)
        assert result == course.organization.inn

    def test_dehydrate_organization_without_organization(self):
        """Тест получения названия организации когда её нет"""
        resource = CourseResource()
        mock_course = type("MockCourse", (), {"organization": None})()
        result = resource.dehydrate_organization__short_name(mock_course)
        assert result == ""

    def test_dehydrate_categories(self, course, category, another_category):
        """Тест получения категорий курса"""
        course.categories.add(category, another_category)
        resource = CourseResource()
        result = resource.dehydrate_categories(course)
        assert category.name in result
        assert another_category.name in result
        assert ", " in result

    def test_dehydrate_is_deleted(self, course):
        """Тест статуса удаления"""
        resource = CourseResource()
        result_active = resource.dehydrate_is_deleted(course)
        assert result_active == "Нет"

        course.is_deleted = True
        result_deleted = resource.dehydrate_is_deleted(course)
        assert result_deleted == "Да"


class TestCourseAdmin:
    """Тесты для админ-класса CourseAdmin"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.admin_site = AdminSite()
        self.course_admin = CourseAdmin(Course, self.admin_site)

    def test_admin_list_display(self):
        """Тест полей списка"""
        expected_fields = (
            "title",
            "organization",
            "program_type",
            "duration_hours",
            "format",
            "status_display",
            "last_parsed",
        )
        assert self.course_admin.list_display == expected_fields

    def test_admin_list_filter(self):
        """Тест фильтров"""
        assert "organization" in self.course_admin.list_filter
        assert "program_type" in self.course_admin.list_filter
        assert "format" in self.course_admin.list_filter
        assert SoftDeleteFilter in self.course_admin.list_filter

    def test_admin_search_fields(self):
        """Тест полей поиска"""
        expected_search = ("title", "description", "organization__short_name")
        assert self.course_admin.search_fields == expected_search

    def test_admin_readonly_fields(self):
        """Тест readonly полей"""
        assert "last_parsed" in self.course_admin.readonly_fields
        assert "deleted_at" in self.course_admin.readonly_fields

    def test_admin_filter_horizontal(self):
        """Тест filter_horizontal настроек"""
        assert "categories" in self.course_admin.filter_horizontal

    def test_admin_export_formats(self):
        """Тест форматов экспорта"""
        expected_formats = ["csv", "xlsx", "json"]
        format_names = [f().get_title().lower() for f in self.course_admin.formats]
        for fmt in expected_formats:
            assert fmt in format_names

    def test_admin_actions(self):
        """Тест наличия действий"""
        actions = self.course_admin.actions
        assert "soft_delete_action" in actions
        assert "restore_action" in actions
        assert "hard_delete_action" in actions

    def test_status_display_method_active(self, course):
        """Тест метода отображения статуса для активного курса"""
        result = self.course_admin.status_display(course)
        assert "Активен" in result
        assert "#28a745" in result

    def test_status_display_method_deleted(self, deleted_course):
        """Тест метода отображения статуса для удалённого курса"""
        result = self.course_admin.status_display(deleted_course)
        assert "Корзина" in result
        assert "#dc3545" in result

    def test_get_urls_includes_custom_urls(self):
        """Тест добавления кастомных URL"""
        urls = self.course_admin.get_urls()
        url_patterns = [str(p.pattern) for p in urls]

        # Проверяем URL парсинга
        assert any("parse-vsuet/" in str(p) for p in urls)
        assert any("parse-vsu/" in str(p) for p in urls)
        assert any("parse-vstu/" in str(p) for p in urls)
        assert any("parse-all/" in str(p) for p in urls)
        # Проверяем URL восстановления и удаления
        assert any("restore/" in str(p) for p in urls)
        assert any("soft-delete/" in str(p) for p in urls)
        assert any("hard-delete/" in str(p) for p in urls)

    def test_soft_delete_action(self, admin_user, course):
        """Тест массового мягкого удаления"""
        request = MockRequest(admin_user)
        queryset = Course.objects.filter(id=course.id)

        self.course_admin.soft_delete_action(request, queryset)

        course.refresh_from_db()
        assert course.is_deleted is True
        assert course.deleted_at is not None

    def test_restore_action(self, admin_user, deleted_course):
        """Тест массового восстановления"""
        request = MockRequest(admin_user)
        queryset = Course.objects.filter(id=deleted_course.id)

        self.course_admin.restore_action(request, queryset)

        deleted_course.refresh_from_db()
        assert deleted_course.is_deleted is False
        assert deleted_course.deleted_at is None

    def test_hard_delete_action(self, admin_user, course):
        """Тест полного удаления"""
        request = MockRequest(admin_user)
        queryset = Course.objects.filter(id=course.id)

        self.course_admin.hard_delete_action(request, queryset)

        assert not Course.objects.filter(id=course.id).exists()

    def test_soft_delete_single_course(self, admin_user, course):
        """Тест мягкого удаления одного курса"""
        request = MockRequest(admin_user)
        response = self.course_admin.soft_delete_single_course(request, course.id)

        course.refresh_from_db()
        assert course.is_deleted is True
        assert isinstance(response, HttpResponseRedirect)

    def test_restore_single_course(self, admin_user, deleted_course):
        """Тест восстановления одного курса"""
        request = MockRequest(admin_user)
        response = self.course_admin.restore_single_course(request, deleted_course.id)

        deleted_course.refresh_from_db()
        assert deleted_course.is_deleted is False
        assert isinstance(response, HttpResponseRedirect)

    def test_hard_delete_single_course(self, admin_user, course):
        """Тест полного удаления одного курса"""
        request = MockRequest(admin_user)
        response = self.course_admin.hard_delete_single_course(request, course.id)

        assert not Course.objects.filter(id=course.id).exists()
        assert isinstance(response, HttpResponseRedirect)

    def test_delete_model_override(self, admin_user, course):
        """Тест переопределённого метода delete_model"""
        request = MockRequest(admin_user)
        self.course_admin.delete_model(request, course)

        course.refresh_from_db()
        assert course.is_deleted is True
        assert course.deleted_at is not None

    def test_delete_queryset_override(self, admin_user, course):
        """Тест переопределённого метода delete_queryset"""
        request = MockRequest(admin_user)
        queryset = Course.objects.filter(id=course.id)
        self.course_admin.delete_queryset(request, queryset)

        course.refresh_from_db()
        assert course.is_deleted is True


class TestCategoryAdmin:
    """Тесты для админ-класса CategoryAdmin"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.admin_site = AdminSite()
        self.category_admin = CategoryAdmin(Category, self.admin_site)

    def test_admin_list_display(self):
        """Тест полей списка"""
        assert "name" in self.category_admin.list_display
        assert "slug" in self.category_admin.list_display

    def test_admin_prepopulated_fields(self):
        """Тест автоматического заполнения slug из name"""
        assert "slug" in self.category_admin.prepopulated_fields
        assert self.category_admin.prepopulated_fields["slug"] == ("name",)

    def test_admin_search_fields(self):
        """Тест полей поиска"""
        assert "name" in self.category_admin.search_fields


class TestParseActionsMixin:
    """Тесты для миксина действий парсинга"""

    def test_parse_vsuet_calls_parser_manager(self, admin_user):
        """Тест вызова парсера ВГУИТ"""
        with patch("apps.courses.admin.ParserManager.run_parser") as mock_parser:
            from apps.courses.admin import ParseActionsMixin

            class TestAdmin(ParseActionsMixin):
                pass

            admin_instance = TestAdmin()
            request = MockRequest(admin_user)
            response = admin_instance.parse_vsuet(request)

            mock_parser.assert_called_once_with("vsuet", request)
            assert response.status_code == 302

    def test_parse_vsu_calls_parser_manager(self, admin_user):
        """Тест вызова парсера ВГУ"""
        with patch("apps.courses.admin.ParserManager.run_parser") as mock_parser:
            from apps.courses.admin import ParseActionsMixin

            class TestAdmin(ParseActionsMixin):
                pass

            admin_instance = TestAdmin()
            request = MockRequest(admin_user)
            response = admin_instance.parse_vsu(request)

            mock_parser.assert_called_once_with("vsu", request)
            assert response.status_code == 302

    def test_parse_vstu_calls_parser_manager(self, admin_user):
        """Тест вызова парсера ВГТУ"""
        with patch("apps.courses.admin.ParserManager.run_parser") as mock_parser:
            from apps.courses.admin import ParseActionsMixin

            class TestAdmin(ParseActionsMixin):
                pass

            admin_instance = TestAdmin()
            request = MockRequest(admin_user)
            response = admin_instance.parse_vstu(request)

            mock_parser.assert_called_once_with("vstu", request)
            assert response.status_code == 302

    def test_parse_all_calls_parser_manager(self, admin_user):
        """Тест вызова парсера всех источников"""
        with patch("apps.courses.admin.ParserManager.run_all_parsers") as mock_all:
            from apps.courses.admin import ParseActionsMixin

            class TestAdmin(ParseActionsMixin):
                pass

            admin_instance = TestAdmin()
            request = MockRequest(admin_user)
            response = admin_instance.parse_all(request)

            mock_all.assert_called_once_with(request)
            assert response.status_code == 302


class TestCourseAdminIntegration:
    """Интеграционные тесты для админки"""

    def test_course_admin_accessible_by_superuser(self, client, admin_user):
        """Тест доступа к админке курсов для суперпользователя"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_changelist")
        response = client.get(url)
        assert response.status_code == 200

    def test_course_admin_not_accessible_by_regular_user(self, client, regular_user):
        """Тест запрета доступа к админке для обычного пользователя"""
        client.force_login(regular_user)
        url = reverse("admin:courses_course_changelist")
        response = client.get(url)
        assert response.status_code == 302

    def test_course_admin_add_page(self, client, admin_user):
        """Тест страницы добавления курса в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_add")
        response = client.get(url)
        assert response.status_code == 200

    def test_course_admin_edit_page(self, client, admin_user, course):
        """Тест страницы редактирования курса в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_change", args=[course.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_course_admin_delete_page(self, client, admin_user, course):
        """Тест страницы удаления курса в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_delete", args=[course.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_course_admin_search(self, client, admin_user, course):
        """Тест поиска в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_changelist")
        response = client.get(url, {"q": course.title})
        assert response.status_code == 200
        assert course.title in response.content.decode()

    def test_course_admin_filter_by_organization(
        self, client, admin_user, course, organization
    ):
        """Тест фильтрации по организации"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_changelist")
        response = client.get(url, {"organization__id__exact": organization.id})
        assert response.status_code == 200

    def test_soft_delete_filter_in_admin(self, admin_client, course, deleted_course):
        """Интеграционный тест фильтрации курсов через админку"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        admin_user = User.objects.get(username="admin")
        admin_client.force_login(admin_user)

        # Убеждаемся, что статусы правильные
        course.is_deleted = False
        course.save()
        deleted_course.is_deleted = True
        deleted_course.save()

        url = reverse("admin:courses_course_changelist")

        # Тест фильтра активных курсов
        response = admin_client.get(url, {"course_status": "active"})
        assert response.status_code == 200
        content = response.content.decode()
        assert course.title in content
        assert deleted_course.title not in content

        # Тест фильтра удалённых курсов
        response = admin_client.get(url, {"course_status": "deleted"})
        assert response.status_code == 200
        content = response.content.decode()
        assert deleted_course.title in content
        assert course.title not in content

        # Тест показа всех курсов
        response = admin_client.get(url, {"course_status": "all"})
        assert response.status_code == 200
        content = response.content.decode()
        assert course.title in content
        assert deleted_course.title in content


class TestCourseResourceIntegration:
    """Интеграционные тесты для экспорта/импорта"""

    def test_export_courses_to_csv(self, client, admin_user, course):
        """Тест экспорта курсов в CSV"""
        client.force_login(admin_user)
        url = reverse("admin:courses_course_changelist")
        response = client.post(
            url, {"action": "export_admin_action", "file_format": "0"}
        )
        assert response.status_code in [200, 302]

    def test_course_resource_export_data(self, course, category):
        """Тест данных экспорта"""
        course.categories.add(category)
        resource = CourseResource()
        dataset = resource.export()

        assert dataset.height >= 1

        headers = dataset.headers
        assert "title" in headers
        assert "organization__short_name" in headers
        assert "is_deleted" in headers
        assert "deleted_at" in headers

    def test_course_resource_returns_correct_export_order(self):
        """Тест порядка полей при экспорте"""
        resource = CourseResource()
        expected_order = (
            "id",
            "title",
            "organization__short_name",
            "organization__inn",
            "program_type",
            "duration_hours",
            "duration_weeks",
            "study_mode",
            "format",
            "teachers",
            "target_audience",
            "topics",
            "start_dates",
            "price",
            "field_of_study",
            "url",
            "last_parsed",
            "is_deleted",
            "deleted_at",
        )
        assert resource._meta.export_order == expected_order


class TestCategoryAdminIntegration:
    """Интеграционные тесты для админки категорий"""

    def test_category_admin_list(self, client, admin_user, category):
        """Тест списка категорий в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_category_changelist")
        response = client.get(url)
        assert response.status_code == 200
        assert category.name in response.content.decode()

    def test_category_admin_add(self, client, admin_user):
        """Тест добавления категории через админку"""
        client.force_login(admin_user)
        url = reverse("admin:courses_category_add")
        response = client.get(url)
        assert response.status_code == 200

        data = {"name": "Тестовая категория", "slug": "test-category"}
        response = client.post(url, data)
        assert response.status_code == 302
        assert Category.objects.filter(name="Тестовая категория").exists()

    def test_category_admin_auto_slug(self, client, admin_user):
        """Тест автоматического заполнения slug в админке"""
        client.force_login(admin_user)
        url = reverse("admin:courses_category_add")
        data = {"name": "Новая категория"}
        response = client.post(url, data)
        assert response.status_code == 302
        category = Category.objects.get(name="Новая категория")
        assert category.slug is not None
