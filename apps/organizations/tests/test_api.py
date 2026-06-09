import pytest
from django.urls import reverse
from rest_framework import status
from apps.organizations.models import District, OrganizationType, Organization


@pytest.mark.django_db
class TestDistrictAPI:
    """Тесты API для районов"""

    def test_list_districts(self, api_client, district, another_district):
        """Тест получения списка районов"""
        url = reverse("district-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["short_name"] in ["САО", "ЦАО", "ЮАО"]

    def test_retrieve_district(self, api_client, district):
        """Тест получения конкретного района"""
        url = reverse("district-detail", args=[district.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["short_name"] == "ЦАО"
        assert response.data["full_name"] == "Центральный административный округ"

    def test_search_districts(self, api_client, district, another_district):
        """Тест поиска районов"""
        url = reverse("district-list")
        response = api_client.get(url, {"search": "Центральный"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["short_name"] == "ЦАО"

    def test_filter_districts(self, api_client, district, another_district):
        """Тест фильтрации районов"""
        url = reverse("district-list")
        response = api_client.get(url, {"ordering": "-short_name"})

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert results[0]["short_name"] > results[-1]["short_name"]


@pytest.mark.django_db
class TestOrganizationTypeAPI:
    """Тесты API для типов организаций"""

    def test_list_organization_types(
        self, api_client, organization_type, another_organization_type
    ):
        """Тест получения списка типов организаций"""
        url = reverse("organizationtype-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        names = [item["name"] for item in response.data["results"]]
        assert "Школа" in names
        assert "Детский сад" in names

    def test_retrieve_organization_type(self, api_client, organization_type):
        """Тест получения конкретного типа организации"""
        url = reverse("organizationtype-detail", args=[organization_type.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Школа"


@pytest.mark.django_db
class TestOrganizationsHtmlAPI:
    """Тесты для HTML API эндпоинтов организаций (api.py)"""

    def test_get_organization_types_html_without_district(self, api_client):
        """Тест получения типов организаций без district_id"""
        url = reverse("get_organization_types_html")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert '<option value="">---------</option>' in response.content.decode()

    def test_get_organization_types_html_with_invalid_district(self, api_client):
        """Тест получения типов организаций с несуществующим district_id"""
        url = reverse("get_organization_types_html")
        response = api_client.get(url, {"district": 99999})

        assert response.status_code == status.HTTP_200_OK
        assert '<option value="">---------</option>' in response.content.decode()

    def test_get_organization_types_html_with_valid_district(
        self, api_client, district, organization
    ):
        """Тест получения типов организаций с валидным district_id"""
        url = reverse("get_organization_types_html")
        response = api_client.get(url, {"district": district.id})

        assert response.status_code == status.HTTP_200_OK
        html = response.content.decode()
        assert '<option value="">---------</option>' in html
        # Проверяем, что тип организации школы присутствует
        assert "Школа" in html

    def test_get_organizations_html_without_params(self, api_client):
        """Тест получения организаций без district и type"""
        url = reverse("get_organizations_html")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert '<option value="">---------</option>' in response.content.decode()

    def test_get_organizations_html_with_invalid_params(self, api_client):
        """Тест получения организаций с несуществующими district и type"""
        url = reverse("get_organizations_html")
        response = api_client.get(url, {"district": 99999, "type": 99999})

        assert response.status_code == status.HTTP_200_OK
        assert '<option value="">---------</option>' in response.content.decode()

    def test_get_organizations_html_with_valid_params(self, api_client, organization):
        """Тест получения организаций с валидными district и type"""
        url = reverse("get_organizations_html")
        response = api_client.get(
            url,
            {
                "district": organization.district.id,
                "type": organization.organization_type.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        html = response.content.decode()
        assert '<option value="">---------</option>' in html
        assert organization.short_name in html

    def test_get_organizations_html_without_matching_organizations(
        self, api_client, district
    ):
        """Тест получения организаций с валидным районом, но без организаций"""
        url = reverse("get_organizations_html")
        response = api_client.get(url, {"district": district.id, "type": 99999})

        assert response.status_code == status.HTTP_200_OK
        html = response.content.decode()
        assert '<option value="">---------</option>' in html
        assert "Школа" not in html


@pytest.mark.django_db
class TestOrganizationAPI:
    """Тесты API для организаций"""

    def test_list_organizations(self, api_client, organization, another_organization):
        """Тест получения списка организаций"""
        url = reverse("organization-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["short_name"] in [
            "ГБОУ Школа №1",
            "ГБДОУ Детский сад №2",
        ]

    def test_retrieve_organization(self, api_client, organization):
        """Тест получения конкретной организации"""
        url = reverse("organization-detail", args=[organization.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["short_name"] == "ГБОУ Школа №1"
        assert response.data["inn"] == "7701234567"
        assert response.data["district"]["short_name"] == "ЦАО"
        assert response.data["organization_type"]["name"] == "Школа"
        assert response.data["status_display"] == "Действующая"

    def test_create_organization_as_anonymous(
        self, api_client, district, organization_type
    ):
        """Тест создания организации анонимным пользователем (должно быть запрещено)"""
        url = reverse("organization-list")
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "kpp": "770101004",
            "ogrn": "1027700123459",
            "district": district.id,
            "organization_type": organization_type.id,
            "address_raw": "г. Москва, ул. Новая, д. 1",
            "status": "ACTIVE",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_organization_as_admin(
        self, api_client, admin_user, district, organization_type
    ):
        """Тест создания организации администратором"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("organization-list")
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "kpp": "770101004",
            "ogrn": "1027700123459",
            "district": district.id,
            "organization_type": organization_type.id,
            "address_raw": "г. Москва, ул. Новая, д. 1",
            "status": "ACTIVE",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["short_name"] == "Новая школа"
        assert response.data["inn"] == "7701234571"

    def test_update_organization(self, api_client, admin_user, organization):
        """Тест обновления организации"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("organization-detail", args=[organization.id])
        data = {"short_name": "Обновленная школа", "status": "LIQUIDATING"}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["short_name"] == "Обновленная школа"
        assert response.data["status"] == "LIQUIDATING"

    def test_delete_organization(self, api_client, admin_user, organization):
        """Тест удаления организации"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("organization-detail", args=[organization.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Organization.objects.filter(id=organization.id).count() == 0

    def test_filter_organizations_by_district(
        self, api_client, organization, another_organization
    ):
        """Тест фильтрации организаций по району"""
        url = reverse("organization-list")
        response = api_client.get(url, {"district": organization.district.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["district_name"] == "ЦАО"

    def test_filter_organizations_by_type(
        self, api_client, organization, another_organization
    ):
        """Тест фильтрации организаций по типу"""
        url = reverse("organization-list")
        response = api_client.get(
            url, {"organization_type": organization.organization_type.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["organization_type_name"] == "Школа"

    def test_filter_organizations_by_status(
        self, api_client, organization, inactive_organization
    ):
        """Тест фильтрации организаций по статусу"""
        url = reverse("organization-list")
        response = api_client.get(url, {"status": "ACTIVE"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "ACTIVE"

    def test_search_organizations(self, api_client, organization, another_organization):
        """Тест поиска организаций"""
        url = reverse("organization-list")
        response = api_client.get(url, {"search": "Школа"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert "Школа" in response.data["results"][0]["short_name"]

    def test_by_district_endpoint(self, api_client, organization, another_organization):
        """Тест кастомного эндпоинта by_district"""
        url = reverse("organization-by-district")
        response = api_client.get(url, {"district_id": organization.district.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["district_name"] == "ЦАО"

    def test_by_district_endpoint_without_district(self, api_client):
        """Тест эндпоинта by_district без district_id"""
        url = reverse("organization-by-district")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_with_coordinates_endpoint(
        self, api_client, organization, another_organization
    ):
        """Тест кастомного эндпоинта with_coordinates"""
        url = reverse("organization-with-coordinates")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for org in response.data:
            assert org["coordinates"] is not None

    def test_with_coordinates_endpoint_empty(self, api_client, db):
        """Тест эндпоинта with_coordinates когда нет организаций с координатами"""
        url = reverse("organization-with-coordinates")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_pagination_works(self, api_client, organization, another_organization):
        """Тест пагинации - проверяем структуру ответа"""
        url = reverse("organization-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Проверяем, что в ответе есть поля пагинации
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data
        # Проверяем количество записей
        assert response.data["count"] == 2
        # Проверяем, что все записи есть на первой странице
        assert len(response.data["results"]) == 2
