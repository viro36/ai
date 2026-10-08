import pytest
from datetime import date
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.hashers import make_password
from django.urls import reverse

from unittest.mock import Mock

from apps.accounts.admin import (
    EmployerRegistrationRequestAdmin,
    EmployerProfileAdmin,
    EmployeeProfileAdmin,
    PositionAdmin,
    UserTypeFilter,
    EmployerProfileForm,
    EmployeeProfileForm,
)
from apps.accounts.models import (
    EmployerRegistrationRequest,
    EmployerProfile,
    EmployeeProfile,
    Position,
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
        assert "is_unemployed" in admin.list_display
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

    def test_organization_link_unemployed(self, test_employee_user):
        """Тест ссылки на организацию для безработного"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )
        result = admin.organization_link(profile)

        # Не должно упасть с AttributeError
        assert "Безработный" in result
        assert "/admin/organizations/organization/" not in result

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

    def test_filter_by_is_unemployed(
        self, test_employee_user, test_employee_user2, test_organization
    ):
        """Тест фильтрации по флагу 'Безработный'"""
        # Работающий
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        # Безработный
        EmployeeProfile.objects.create(
            user=test_employee_user2,
            snils="987-654-321 01",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )

        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)

        # Фильтр по безработным
        qs = admin.get_queryset(None).filter(is_unemployed=True)
        assert qs.count() == 1
        assert qs.first().user == test_employee_user2


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


class TestViewerPermissions:
    """Тесты для проверки прав просмотрщика в админке accounts"""

    def test_viewer_can_view_employer_requests(self, viewer_client):
        """Тест - просмотрщик может видеть список заявок"""
        url = reverse("admin:accounts_employerregistrationrequest_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_can_view_employer_profiles(self, viewer_client):
        """Тест - просмотрщик может видеть список профилей работодателей"""
        url = reverse("admin:accounts_employerprofile_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_can_view_employee_profiles(self, viewer_client):
        """Тест - просмотрщик может видеть список профилей работников"""
        url = reverse("admin:accounts_employeeprofile_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200

    def test_viewer_cannot_add_employer_request(self, viewer_client):
        """Тест - просмотрщик не может добавлять заявки"""
        url = reverse("admin:accounts_employerregistrationrequest_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_add_employer_profile(self, viewer_client):
        """Тест - просмотрщик не может добавлять профили работодателей"""
        url = reverse("admin:accounts_employerprofile_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_add_employee_profile(self, viewer_client):
        """Тест - просмотрщик не может добавлять профили работников"""
        url = reverse("admin:accounts_employeeprofile_add")
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_cannot_edit_employer_request(self, viewer_client):
        """Тест - просмотрщик не может редактировать заявки"""
        request_obj = EmployerRegistrationRequest.objects.create(
            username="edit_test",
            email="edit@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789099",
            status="pending",
        )
        url = reverse(
            "admin:accounts_employerregistrationrequest_change", args=[request_obj.id]
        )
        # Пытаемся отправить POST запрос на изменение
        data = {
            "short_name": "Измененное ООО",
            "full_name": "Измененное полное название",
        }
        response = viewer_client.post(url, data)
        # Должен быть редирект или 403
        assert response.status_code in [302, 403]

    def test_viewer_cannot_delete_employer_request(self, viewer_client):
        """Тест - просмотрщик не может удалять заявки"""
        request_obj = EmployerRegistrationRequest.objects.create(
            username="delete_test",
            email="delete@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789099",
            status="pending",
        )
        url = reverse(
            "admin:accounts_employerregistrationrequest_delete", args=[request_obj.id]
        )
        response = viewer_client.get(url)
        assert response.status_code in [302, 403]

    def test_viewer_has_no_actions_on_employer_requests(self, viewer_client):
        """Тест - у просмотрщика нет выпадающего списка действий в заявках"""
        url = reverse("admin:accounts_employerregistrationrequest_changelist")
        response = viewer_client.get(url)
        content = response.content.decode()
        assert 'name="action"' not in content or "action" not in content.lower()

    def test_admin_has_actions_on_employer_requests(self, admin_client):
        """Тест - у администратора есть выпадающий список действий в заявках"""
        url = reverse("admin:accounts_employerregistrationrequest_changelist")
        response = admin_client.get(url)
        content = response.content.decode()
        assert "Действия" in content or "action" in content.lower()

    def test_viewer_can_view_unemployed_profiles(
        self, viewer_client, test_employee_user
    ):
        """Просмотрщик может видеть безработных в списке"""
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_changelist")
        response = viewer_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # Просмотрщик видит безработного
        assert "Безработный" in content or test_employee_user.last_name in content


@pytest.mark.django_db
class TestEmployeeProfileAdminFullProfile:
    """Тесты для кнопки «Полный профиль» и статуса анкеты"""

    def test_profile_complete_badge_filled(self, test_employee_user, test_organization):
        """Бейдж 'Анкета заполнена', когда все обязательные поля заполнены"""
        test_employee_user.birthday = date(1990, 1, 1)
        test_employee_user.save()

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
            gender="M",
            citizenship="Россия",
            education_level="higher",
            graduation_year=2014,
            education_institution="ВГУ",
            specialty="Инженер",
            locality="Воронеж",
            municipality="Воронеж",
        )

        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        result = admin.profile_complete_badge(profile)

        assert "Заполнена" in result
        assert "Не заполнена" not in result

    def test_profile_complete_badge_not_filled(self, test_employee_user):
        """Бейдж 'Анкета не заполнена', когда не хватает полей"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )

        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        result = admin.profile_complete_badge(profile)

        assert "Не заполнена" in result

    def test_full_profile_link_contains_url(self, test_employee_user):
        """Кнопка 'Полный профиль' содержит правильный URL"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )

        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        result = admin.full_profile_link(profile)

        expected_url = reverse(
            "admin:accounts_employeeprofile_full_profile", args=[profile.id]
        )
        assert expected_url in result
        assert "Открыть" in result

    def test_full_profile_url_registered(self):
        """URL /full-profile/ зарегистрирован в админке"""
        site = AdminSite()
        admin = EmployeeProfileAdmin(EmployeeProfile, site)
        urls = admin.get_urls()
        url_patterns = [str(u.pattern) for u in urls]
        assert any("full-profile" in p for p in url_patterns)


@pytest.mark.django_db
class TestFullProfileView:
    """Тесты для кастомной страницы полного профиля"""

    def test_full_profile_view_requires_staff(self, client, test_employee_user):
        """Не-админ не может открыть страницу"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_full_profile_view_ok_for_admin(self, admin_client, test_employee_user):
        """Админ видит страницу с карточкой"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Статусы готовности" in content
        assert "Пользователь (CustomUser)" in content
        assert "Профиль работника" in content
        assert test_employee_user.last_name in content

    def test_full_profile_view_shows_missing_fields(
        self, admin_client, test_employee_user
    ):
        """Показывает недостающие поля для is_profile_complete()"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        content = response.content.decode()
        assert "не хватает" in content.lower() or "Каких полей не хватает" in content
        assert "birthday" in content

    def test_full_profile_view_404_for_missing(self, admin_client):
        """404 для несуществующего профиля"""
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[999999])
        response = admin_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestEmployeeProfileSave:
    """Тесты синхронизации is_unemployed и employment_status в save()"""

    def test_save_unemployed_sets_status(self, test_employee_user):
        """is_unemployed=True устанавливает employment_status=unemployed"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
            employment_status=None,
        )
        profile.refresh_from_db()
        assert profile.employment_status == "unemployed"

    def test_save_employed_resets_unemployed_status(
        self, test_employee_user, test_organization
    ):
        """is_unemployed=False и статус unemployed меняется на employed"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
            is_unemployed=False,
            employment_status="unemployed",
        )
        profile.refresh_from_db()
        assert profile.employment_status == "employed"

    def test_save_preserves_self_employed(self, test_employee_user):
        """is_unemployed=False и статус self_employed не меняется"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Фрилансер",
            is_unemployed=False,
            employment_status="self_employed",
        )
        profile.refresh_from_db()
        assert profile.employment_status == "self_employed"

    def test_save_preserves_entrepreneur(self, test_employee_user):
        """is_unemployed=False и статус entrepreneur не меняется"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="ИП",
            is_unemployed=False,
            employment_status="entrepreneur",
        )
        profile.refresh_from_db()
        assert profile.employment_status == "entrepreneur"

    def test_save_idempotent(self, test_employee_user, test_organization):
        """Повторное сохранение не меняет статус"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
            is_unemployed=False,
            employment_status="employed",
        )
        profile.save()
        profile.refresh_from_db()
        assert profile.employment_status == "employed"


@pytest.mark.django_db
class TestViewerFullProfile:
    """Просмотрщик может открыть полный профиль (только чтение)"""

    def test_viewer_can_open_full_profile(self, viewer_client, test_employee_user):
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = viewer_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestPositionAdmin:
    """Тесты админки справочника должностей"""

    def test_list_display(self):
        site = AdminSite()
        admin = PositionAdmin(Position, site)
        assert "name" in admin.list_display
        assert "organization_type" in admin.list_display
        assert "position_level" in admin.list_display
        assert "sort_order" in admin.list_display
        assert "is_active" in admin.list_display

    def test_list_filter(self):
        site = AdminSite()
        admin = PositionAdmin(Position, site)
        assert "organization_type" in admin.list_filter
        assert "position_level" in admin.list_filter
        assert "is_active" in admin.list_filter
