import pytest
from django.db.models import Count
from apps.organizations.models import District, OrganizationType, Organization
from apps.organizations.serializers import (
    DistrictSerializer,
    OrganizationTypeSerializer,
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateUpdateSerializer,
)


@pytest.mark.django_db
class TestDistrictSerializer:
    """Тесты сериализатора для районов"""

    def test_district_serializer(self, district):
        """Тест базовой сериализации района"""
        district_with_count = (
            District.objects.filter(id=district.id)
            .annotate(organizations_count=Count("organization"))
            .first()
        )

        serializer = DistrictSerializer(district_with_count)
        data = serializer.data

        assert data["id"] == district.id
        assert data["short_name"] == "ЦАО"
        assert data["full_name"] == "Центральный административный округ"
        assert "organizations_count" in data
        assert data["organizations_count"] == 0


@pytest.mark.django_db
class TestOrganizationTypeSerializer:
    """Тесты сериализатора для типов организаций"""

    def test_organization_type_serializer(self, organization_type):
        """Тест базовой сериализации типа организации"""
        org_type_with_count = (
            OrganizationType.objects.filter(id=organization_type.id)
            .annotate(organizations_count=Count("organization"))
            .first()
        )

        serializer = OrganizationTypeSerializer(org_type_with_count)
        data = serializer.data

        assert data["id"] == organization_type.id
        assert data["name"] == "Школа"
        assert "organizations_count" in data
        assert data["organizations_count"] == 0


@pytest.mark.django_db
class TestOrganizationListSerializer:
    """Тесты сериализатора списка организаций"""

    def test_organization_list_serializer(self, organization):
        """Тест сериализации списка организаций"""
        serializer = OrganizationListSerializer(organization)
        data = serializer.data

        assert data["id"] == organization.id
        assert data["short_name"] == "ГБОУ Школа №1"
        assert data["inn"] == "7701234567"
        assert data["kpp"] == "770101001"
        assert data["ogrn"] == "1027700123456"
        assert data["district_name"] == "ЦАО"
        assert data["organization_type_name"] == "Школа"
        assert data["status"] == "ACTIVE"
        assert data["status_display"] == "Действующая"
        assert data["coordinates"] == "55.7558, 37.6173"
        assert data["coordinates_list"] == [55.7558, 37.6173]
        assert data["address_raw"] == "г. Москва, ул. Ленина, д. 1"

    def test_organization_list_serializer_no_coordinates(self, inactive_organization):
        """Тест сериализации организации без координат"""
        serializer = OrganizationListSerializer(inactive_organization)
        data = serializer.data

        assert data["coordinates"] is None
        assert data["coordinates_list"] is None


@pytest.mark.django_db
class TestOrganizationDetailSerializer:
    """Тесты сериализатора детальной информации организации"""

    def test_organization_detail_serializer(self, organization):
        """Тест детальной сериализации организации"""
        serializer = OrganizationDetailSerializer(organization)
        data = serializer.data

        assert data["id"] == organization.id
        assert data["short_name"] == "ГБОУ Школа №1"
        assert data["inn"] == "7701234567"
        assert data["kpp"] == "770101001"
        assert data["kpp_largest"] == "770101002"
        assert data["ogrn"] == "1027700123456"
        assert data["ogrn_date"] == "2000-01-01"
        assert data["hid"] == "test_hid_123"
        assert data["org_type"] == "LEGAL"
        assert data["opf_code"] == "12345"
        assert data["opf_full"] == "Общество с ограниченной ответственностью"
        assert data["opf_short"] == "ООО"
        assert data["district"]["id"] == organization.district.id
        assert data["district"]["short_name"] == "ЦАО"
        assert data["organization_type"]["id"] == organization.organization_type.id
        assert data["organization_type"]["name"] == "Школа"
        assert data["status"] == "ACTIVE"
        assert data["status_code"] == "1"
        assert data["status_display"] == "Действующая"
        assert data["coordinates"] == "55.7558, 37.6173"
        assert data["coordinates_list"] == [55.7558, 37.6173]
        assert data["address_raw"] == "г. Москва, ул. Ленина, д. 1"
        assert data["postal_code"] == "101000"
        assert data["region"] == "г. Москва"
        assert data["city"] == "Москва"
        assert data["street"] == "ул. Ленина"
        assert data["house"] == "1"
        assert data["okpo"] == "12345678"
        assert data["okved"] == "85.13"
        assert data["manager_name"] == "Петров Петр Петрович"
        assert data["manager_post"] == "Директор"
        assert data["branch_count"] == 5
        assert data["branch_type"] == "MAIN"
        assert data["actuality_date"] == "2024-01-01"
        assert data["registration_date"] == "1999-01-01"
        assert data["liquidation_date"] is None

    def test_organization_detail_full_address(self, organization):
        """Тест формирования полного адреса"""
        serializer = OrganizationDetailSerializer(organization)
        data = serializer.data
        assert data["full_address"] == "101000, г. Москва, Москва, ул. Ленина, 1"

    def test_organization_detail_full_address_empty(self, db):
        """Тест формирования полного адреса с пустыми компонентами"""
        org = Organization.objects.create(
            inn="9999999999",
            short_name="Тест",
            full_name="Тестовая организация",
            address_raw="Только строка адреса",
        )
        serializer = OrganizationDetailSerializer(org)
        data = serializer.data
        assert data["full_address"] == "Только строка адреса"


@pytest.mark.django_db
class TestOrganizationCreateUpdateSerializer:
    """Тесты сериализатора создания/обновления организаций"""

    def test_organization_create_serializer_valid(self, district, organization_type):
        """Тест валидных данных для создания"""
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
            "okpo": "12345678",
            "okved": "85.13",
            "manager_name": "Новый директор",
            "branch_count": 10,
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["short_name"] == "Новая школа"
        assert serializer.validated_data["inn"] == "7701234571"
        assert serializer.validated_data["okpo"] == "12345678"
        assert serializer.validated_data["manager_name"] == "Новый директор"
        assert serializer.validated_data["branch_count"] == 10

    def test_organization_create_serializer_invalid_inn(self, district):
        """Тест невалидного ИНН"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "123",
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "inn" in serializer.errors

    def test_organization_create_serializer_invalid_inn_chars(self, district):
        """Тест ИНН с буквами"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "abc123",
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "inn" in serializer.errors

    def test_organization_create_serializer_invalid_ogrn(self, district):
        """Тест невалидного ОГРН"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "ogrn": "123",
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "ogrn" in serializer.errors

    def test_organization_create_serializer_invalid_kpp(self, district):
        """Тест невалидного КПП"""
        data = {
            "short_name": "Новая школа",
            "full_name": "Новая школа №3",
            "inn": "7701234571",
            "kpp": "123",
            "address_raw": "г. Москва, ул. Новая, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "kpp" in serializer.errors

    def test_organization_create_serializer_minimal_fields(self, db):
        """Тест минимальных обязательных полей"""
        data = {
            "short_name": "Минимальная организация",
            "full_name": "Минимальная организация",
            "inn": "7701234572",
            "address_raw": "г. Москва, ул. Минимальная, д. 1",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert serializer.is_valid()

        organization = serializer.save()
        assert organization.short_name == "Минимальная организация"
        assert organization.district is None
        assert organization.organization_type is None
        assert organization.status is None

    def test_organization_create_all_fields(self, district, organization_type):
        """Тест создания с максимальным количеством полей"""
        data = {
            "short_name": "Полная организация",
            "full_name": "Полная организация",
            "inn": "7701234573",
            "kpp": "770101005",
            "kpp_largest": "770101006",
            "ogrn": "1027700123460",
            "org_type": "LEGAL",
            "full_name_without_opf": "Полная организация без ОПФ",
            "short_name_without_opf": "Полная краткое без ОПФ",
            "latin_name": "Full Organization",
            "opf_code": "12346",
            "opf_full": "Полное ОПФ",
            "opf_short": "Краткое ОПФ",
            "district": district.id,
            "organization_type": organization_type.id,
            "status": "ACTIVE",
            "status_code": "1",
            "coordinates": "55.7558, 37.6173",
            "address_raw": "г. Москва, ул. Полная, д. 1",
            "address_source": "г Москва ул Полная д 1",
            "address_qc": "0",
            "postal_code": "101000",
            "region": "г. Москва",
            "city": "Москва",
            "street": "ул. Полная",
            "house": "1",
            "okpo": "87654321",
            "okato": "12345678902",
            "oktmo": "12345678902",
            "okogu": "54321",
            "okfs": "16",
            "okved": "85.13",
            "okved_type": "2014",
            "manager_name": "Полный Директор",
            "manager_post": "Генеральный директор",
            "branch_count": 15,
            "branch_type": "MAIN",
        }
        serializer = OrganizationCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        organization = serializer.save()
        assert organization.inn == "7701234573"
        assert organization.kpp_largest == "770101006"
        assert organization.org_type == "LEGAL"
        assert organization.latin_name == "Full Organization"
        assert organization.okpo == "87654321"
        assert organization.manager_name == "Полный Директор"
        assert organization.branch_count == 15
