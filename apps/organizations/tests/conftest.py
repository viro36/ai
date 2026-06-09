import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.organizations.models import District, OrganizationType, Organization

User = get_user_model()


@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Фикстура для администратора"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin123"
    )


@pytest.fixture
def regular_user(db):
    """Фикстура для обычного пользователя"""
    return User.objects.create_user(
        username="user", email="user@example.com", password="user123"
    )


@pytest.fixture
def district(db):
    """Фикстура для района"""
    return District.objects.create(
        full_name="Центральный административный округ", short_name="ЦАО"
    )


@pytest.fixture
def another_district(db):
    """Фикстура для другого района"""
    return District.objects.create(
        full_name="Южный административный округ", short_name="ЮАО"
    )


@pytest.fixture
def organization_type(db):
    """Фикстура для типа организации"""
    return OrganizationType.objects.create(name="Школа")


@pytest.fixture
def another_organization_type(db):
    """Фикстура для другого типа организации"""
    return OrganizationType.objects.create(name="Детский сад")


@pytest.fixture
def organization(db, district, organization_type):
    """Фикстура для организации"""
    return Organization.objects.create(
        inn="7701234567",
        kpp="770101001",
        kpp_largest="770101002",
        ogrn="1027700123456",
        ogrn_date="2000-01-01",
        hid="test_hid_123",
        org_type="LEGAL",
        full_name="Государственное бюджетное общеобразовательное учреждение Школа №1",
        short_name="ГБОУ Школа №1",
        full_name_without_opf="Школа №1",
        short_name_without_opf="Школа №1",
        latin_name="School No1",
        fio_surname="Иванов",
        fio_name="Иван",
        fio_patronymic="Иванович",
        opf_code="12345",
        opf_full="Общество с ограниченной ответственностью",
        opf_short="ООО",
        opf_type="2014",
        organization_type=organization_type,
        district=district,
        address_raw="г. Москва, ул. Ленина, д. 1",
        address_source="г Москва ул Ленина д 1",
        address_qc="0",
        postal_code="101000",
        region="г. Москва",
        city="Москва",
        street="ул. Ленина",
        house="1",
        coordinates="55.7558, 37.6173",
        status="ACTIVE",
        status_code="1",
        actuality_date="2024-01-01",
        registration_date="1999-01-01",
        liquidation_date=None,
        okpo="12345678",
        okato="12345678901",
        oktmo="12345678901",
        okogu="12345",
        okfs="16",
        okved="85.13",
        okved_type="2014",
        manager_name="Петров Петр Петрович",
        manager_post="Директор",
        manager_start_date="2015-01-01",
        branch_count=5,
        branch_type="MAIN",
    )


@pytest.fixture
def another_organization(db, another_district, another_organization_type):
    """Фикстура для другой организации"""
    return Organization.objects.create(
        inn="7701234568",
        kpp="770101002",
        ogrn="1027700123457",
        full_name="Государственное бюджетное дошкольное образовательное учреждение Детский сад №2",
        short_name="ГБДОУ Детский сад №2",
        organization_type=another_organization_type,
        district=another_district,
        address_raw="г. Москва, ул. Пушкина, д. 2",
        postal_code="101001",
        region="г. Москва",
        city="Москва",
        street="ул. Пушкина",
        house="2",
        coordinates="55.7559, 37.6174",
        status="ACTIVE",
    )


@pytest.fixture
def inactive_organization(db, district, organization_type):
    """Фикстура для неактивной организации"""
    return Organization.objects.create(
        inn="7701234569",
        kpp="770101003",
        ogrn="1027700123458",
        full_name="Ликвидированная организация",
        short_name="ООО Ромашка",
        organization_type=organization_type,
        district=district,
        address_raw="г. Москва, ул. Гоголя, д. 3",
        status="LIQUIDATED",
    )
