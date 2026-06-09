import pytest
from django.contrib.admin.sites import AdminSite
from apps.organizations.admin import (
    DistrictAdmin,
    OrganizationTypeAdmin,
    OrganizationAdmin,
)
from apps.organizations.models import District, OrganizationType, Organization


class TestDistrictAdmin:
    """Тесты для админки районов"""

    @pytest.mark.django_db
    def test_district_admin_list_display(self):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = DistrictAdmin(District, site)

        assert "short_name" in admin.list_display
        assert "full_name" in admin.list_display
        assert "organizations_count" in admin.list_display

    @pytest.mark.django_db
    def test_district_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = DistrictAdmin(District, site)

        assert "short_name" in admin.search_fields
        assert "full_name" in admin.search_fields


class TestOrganizationTypeAdmin:
    """Тесты для админки типов организаций"""

    @pytest.mark.django_db
    def test_organization_type_admin_list_display(self):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = OrganizationTypeAdmin(OrganizationType, site)

        assert "name" in admin.list_display
        assert "organizations_count" in admin.list_display

    @pytest.mark.django_db
    def test_organization_type_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = OrganizationTypeAdmin(OrganizationType, site)

        assert "name" in admin.search_fields


class TestOrganizationAdmin:
    """Тесты для админки организаций"""

    @pytest.mark.django_db
    def test_organization_admin_list_display(self):
        """Тест отображения полей в списке"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "short_name" in admin.list_display
        assert "inn" in admin.list_display
        assert "status_colored" in admin.list_display
        assert "district_link" in admin.list_display
        assert "organization_type_link" in admin.list_display
        assert "show_map_link" in admin.list_display

    @pytest.mark.django_db
    def test_organization_admin_search_fields(self):
        """Тест полей поиска"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "short_name" in admin.search_fields
        assert "full_name" in admin.search_fields
        assert "inn" in admin.search_fields
        assert "ogrn" in admin.search_fields

    @pytest.mark.django_db
    def test_organization_admin_list_filter(self):
        """Тест фильтров"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        assert "status" in admin.list_filter
        assert "organization_type" in admin.list_filter
        assert "district" in admin.list_filter

    @pytest.mark.django_db
    def test_organization_admin_actions(self):
        """Тест наличия действий"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        # Исправлено: actions содержит строки, а не функции
        assert "update_from_dadata" in admin.actions

    @pytest.mark.django_db
    def test_status_colored_method(self, organization):
        """Тест цветного отображения статуса"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        result = admin.status_colored(organization)
        assert "green" in result
        assert "Действующая" in result

    @pytest.mark.django_db
    def test_district_link_method(self, organization):
        """Тест ссылки на район"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        result = admin.district_link(organization)
        assert (
            f"/admin/organizations/district/{organization.district.id}/change/"
            in result
        )
        assert "ЦАО" in result

    @pytest.mark.django_db
    def test_organization_type_link_method(self, organization, organization_type):
        """Тест ссылки на тип организации"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        result = admin.organization_type_link(organization)
        assert (
            f"/admin/organizations/organizationtype/{organization_type.id}/change/"
            in result
        )
        assert "Школа" in result

    @pytest.mark.django_db
    def test_show_map_link_method_with_coordinates(self, organization):
        """Тест ссылки на карту при наличии координат"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        result = admin.show_map_link(organization)
        assert "yandex.ru/maps" in result
        assert "37.6173" in result
        assert "55.7558" in result

    @pytest.mark.django_db
    def test_show_map_link_method_without_coordinates(self, db):
        """Тест ссылки на карту при отсутствии координат"""
        site = AdminSite()
        admin = OrganizationAdmin(Organization, site)

        org = Organization.objects.create(
            inn="7777777777",
            short_name="Нет координат",
            full_name="Организация без координат",
        )
        result = admin.show_map_link(org)
        assert result == "Нет координат"
