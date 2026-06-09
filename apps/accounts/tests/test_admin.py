import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.hashers import make_password
from unittest.mock import Mock
from apps.accounts.admin import (
    EmployerRegistrationRequestAdmin,
    EmployerProfileAdmin,
    EmployeeProfileAdmin,
    UserTypeFilter,
    EmployerProfileForm,
    EmployeeProfileForm,
)
from apps.accounts.models import (
    EmployerRegistrationRequest,
    EmployerProfile,
    EmployeeProfile,
)


@pytest.mark.django_db
class TestEmployerRegistrationRequestAdmin:
    """Тесты для админки заявок на регистрацию работодателя"""

    def test_list_display(self):
        """Тест отображаемых полей"""
        site = AdminSite()
        admin = EmployerRegistrationRequestAdmin(EmployerRegistrationRequest, site)
        assert "id" in admin.list_display
        assert "short_name" in admin.list_display
        assert "inn" in admin.list_display
        assert "username" in admin.list_display
        assert "email" in admin.list_display
        assert "status" in admin.list_display
        assert "created_at" in admin.list_display

    def test_list_filter(self):
        """Тест фильтров"""
        site = AdminSite()
        admin = EmployerRegistrationRequestAdmin(EmployerRegistrationRequest, site)
        assert "status" in admin.list_filter
        assert "created_at" in admin.list_filter

    def test_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = EmployerRegistrationRequestAdmin(EmployerRegistrationRequest, site)
        assert "short_name" in admin.search_fields
        assert "full_name" in admin.search_fields
        assert "inn" in admin.search_fields
        assert "username" in admin.search_fields
        assert "email" in admin.search_fields

    def test_approve_selected_action(self, admin_user, test_organization):
        """Тест массового одобрения заявок"""
        site = AdminSite()
        admin = EmployerRegistrationRequestAdmin(EmployerRegistrationRequest, site)

        # Создаём заявку
        request_obj = EmployerRegistrationRequest.objects.create(
            username="approve_test",
            email="approve@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789099",
            status="pending",
        )

        queryset = EmployerRegistrationRequest.objects.filter(id=request_obj.id)
        mock_request = Mock()
        mock_request.user = admin_user

        admin.approve_selected(mock_request, queryset)

        request_obj.refresh_from_db()
        assert request_obj.status == "approved"

    def test_reject_selected_action(self, admin_user):
        """Тест массового отклонения заявок"""
        site = AdminSite()
        admin = EmployerRegistrationRequestAdmin(EmployerRegistrationRequest, site)

        request_obj = EmployerRegistrationRequest.objects.create(
            username="reject_test",
            email="reject@test.com",
            password=make_password("testpass"),
            short_name="ООО Отклоняемое",
            full_name="Общество с ограниченной ответственностью Отклоняемое",
            inn="123456789088",
            status="pending",
        )

        queryset = EmployerRegistrationRequest.objects.filter(id=request_obj.id)
        mock_request = Mock()
        mock_request.user = admin_user

        admin.reject_selected(mock_request, queryset)

        request_obj.refresh_from_db()
        assert request_obj.status == "rejected"


@pytest.mark.django_db
class TestUserTypeFilter:
    """Тесты для фильтра по типу пользователя"""

    def test_lookups(self):
        """Тест опций фильтра"""
        filter_obj = UserTypeFilter(None, {}, None, None)
        lookups = filter_obj.lookups(None, None)
        assert ("employer", "Работодатель") in lookups
        assert ("university", "ВУЗ") in lookups

    def test_queryset_filter_employer(self, test_employer_user, test_university_user):
        """Тест фильтрации по работодателям"""
        filter_obj = UserTypeFilter(None, {}, None, None)
        queryset = EmployerProfile.objects.all()

        # Создаём профили
        EmployerProfile.objects.create(user=test_employer_user)

        result = filter_obj.queryset(None, queryset)
        # При value=None возвращает весь queryset
        assert result.count() == 1

    def test_queryset_filter_university(self, test_university_user):
        """Тест фильтрации по ВУЗам"""
        filter_obj = UserTypeFilter(None, {}, None, None)
        queryset = EmployerProfile.objects.all()

        EmployerProfile.objects.create(user=test_university_user)

        result = filter_obj.queryset(None, queryset)
        assert result.count() == 1


@pytest.mark.django_db
class TestEmployerProfileAdmin:
    """Тесты для админки профилей работодателей"""

    def test_list_display(self):
        """Тест отображаемых полей"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)
        assert "id" in admin.list_display
        assert "user_link" in admin.list_display
        assert "org_name" in admin.list_display
        assert "org_type_display" in admin.list_display
        assert "phone" in admin.list_display
        assert "email" in admin.list_display
        assert "contact_person" in admin.list_display
        assert "created_at" in admin.list_display

    def test_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)
        assert "user__username" in admin.search_fields
        assert "user__email" in admin.search_fields
        assert "phone" in admin.search_fields
        assert "email" in admin.search_fields

    def test_user_link(self, test_employer_user):
        """Тест ссылки на пользователя"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)

        profile = EmployerProfile.objects.create(user=test_employer_user)
        result = admin.user_link(profile)

        assert test_employer_user.username in result
        assert f"/admin/users/customuser/{test_employer_user.id}/change/" in result

    def test_org_name(self, test_employer_user, test_organization):
        """Тест названия организации"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)

        profile = EmployerProfile.objects.create(user=test_employer_user)
        result = admin.org_name(profile)

        assert test_organization.short_name in result

    def test_org_type_display_employer(self, test_employer_user):
        """Тест отображения типа - работодатель"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)

        profile = EmployerProfile.objects.create(user=test_employer_user)
        result = admin.org_type_display(profile)

        assert "Работодатель" in result

    def test_org_type_display_university(self, test_university_user):
        """Тест отображения типа - ВУЗ"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)

        profile = EmployerProfile.objects.create(user=test_university_user)
        result = admin.org_type_display(profile)

        assert "ВУЗ" in result

    def test_contact_person(self, test_employer_user):
        """Тест контактного лица"""
        site = AdminSite()
        admin = EmployerProfileAdmin(EmployerProfile, site)

        profile = EmployerProfile.objects.create(
            user=test_employer_user,
            contact_person_full_name="Иванов Иван Иванович",
            contact_person_phone="+7 999 123-45-67",
        )
        result = admin.contact_person(profile)

        assert "Иванов Иван Иванович" in result
        assert "+7 999 123-45-67" in result


@pytest.mark.django_db
class TestEmployeeProfileAdmin:
    """Тесты для админки профилей работников"""

    def test_list_display(self):
        """Тест отображаемых полей"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        assert "id" in admin.list_display
        assert "user_link" in admin.list_display
        assert "organization_link" in admin.list_display
        assert "position_level_display" in admin.list_display
        assert "employment_status" in admin.list_display
        assert "education_level" in admin.list_display
        assert "created_at" in admin.list_display

    def test_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        assert "user__last_name" in admin.search_fields
        assert "user__first_name" in admin.search_fields
        assert "user__snils" in admin.search_fields
        assert "organization__short_name" in admin.search_fields
        assert "specialty" in admin.search_fields

    def test_user_link(self, test_employee_user, test_organization):
        """Тест ссылки на пользователя"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        result = admin.user_link(profile)

        assert test_employee_user.get_full_name() in result
        assert f"/admin/users/customuser/{test_employee_user.id}/change/" in result

    def test_organization_link(self, test_employee_user, test_organization):
        """Тест ссылки на организацию"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        result = admin.organization_link(profile)

        assert test_organization.short_name in result
        assert (
            f"/admin/organizations/organization/{test_organization.id}/change/"
            in result
        )

    def test_position_level_display(self, test_employee_user, test_organization):
        """Тест отображения категории должности"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        result = admin.position_level_display(profile)

        assert result == "Специалист"


@pytest.mark.django_db
class TestEmployerProfileForm:
    """Тесты для формы EmployerProfileForm"""

    def test_form_valid(self, test_employer_user):
        """Тест валидной формы"""
        form = EmployerProfileForm(instance=EmployerProfile(user=test_employer_user))
        assert form.fields["user"].queryset.count() >= 1

    def test_form_initial_value(self, test_employer_user):
        """Тест начального значения при редактировании"""
        profile = EmployerProfile.objects.create(user=test_employer_user)
        form = EmployerProfileForm(instance=profile)
        # Проверяем, что форма создалась без ошибок
        assert form.instance.user == test_employer_user


@pytest.mark.django_db
class TestEmployeeProfileForm:
    """Тесты для формы EmployeeProfileForm"""

    def test_form_valid(self, test_employee_user):
        """Тест валидной формы"""
        form = EmployeeProfileForm()
        assert form.fields["user"].queryset is not None

    def test_form_queryset_filter(self, test_employee_user, test_employer_user):
        """Тест фильтрации пользователей только работниками"""
        form = EmployeeProfileForm()
        queryset = form.fields["user"].queryset

        assert queryset.filter(id=test_employee_user.id).exists()
        assert not queryset.filter(id=test_employer_user.id).exists()
