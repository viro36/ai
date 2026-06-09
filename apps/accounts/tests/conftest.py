import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course
from apps.organizations.models import Organization, District, OrganizationType

User = get_user_model()


@pytest.fixture
def test_district():
    """Фикстура для района"""
    return District.objects.create(full_name="Центральный район", short_name="ЦАО")


@pytest.fixture
def test_organization_type():
    """Фикстура для типа организации"""
    return OrganizationType.objects.create(name="ООО")


@pytest.fixture
def test_organization(test_district, test_organization_type):
    """Фикстура для организации"""
    return Organization.objects.create(
        inn="123456789012",
        kpp="123456789",
        ogrn="123456789012345",
        full_name="Общество с ограниченной ответственностью Тест",
        short_name="ООО Тест",
        organization_type=test_organization_type,
        district=test_district,
        address_raw="г. Москва, ул. Тестовая, д. 1",
        status="ACTIVE",
    )


@pytest.fixture
def regular_user(db):
    """Фикстура для обычного пользователя"""
    return User.objects.create_user(
        username="regular_user",
        email="regular@test.com",
        password="regular123",
        user_type="regular",
    )


@pytest.fixture
def admin_user(db):
    """Фикстура для администратора"""
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="admin123",
    )


@pytest.fixture
def test_employer_user(test_organization):
    """Фикстура для пользователя-работодателя"""
    user = User.objects.create_user(
        username="test_employer",
        email="employer@test.com",
        password="testpass123",
        user_type="employer",
        organization=test_organization,
        last_name="Иванов",
        first_name="Иван",
    )
    return user


@pytest.fixture
def test_university_user(test_organization):
    """Фикстура для пользователя-ВУЗа"""
    user = User.objects.create_user(
        username="test_university",
        email="university@test.com",
        password="testpass123",
        user_type="university",
        organization=test_organization,
        last_name="Петров",
        first_name="Петр",
    )
    return user


@pytest.fixture
def test_employee_user(test_organization):
    """Фикстура для пользователя-работника"""
    user = User.objects.create_user(
        username="test_employee",
        email="employee@test.com",
        password="testpass123",
        user_type="employee",
        organization=test_organization,
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        snils="123-456-789 01",
    )
    return user


@pytest.fixture
def test_employee_user2(test_organization):
    """Фикстура для второго пользователя-работника"""
    user = User.objects.create_user(
        username="test_employee2",
        email="employee2@test.com",
        password="testpass123",
        user_type="employee",
        organization=test_organization,
        last_name="Петров",
        first_name="Петр",
        patronymic="Петрович",
        snils="987-654-321 01",
    )
    return user


@pytest.fixture
def test_employee_user_with_profile(test_employee_user, test_organization):
    """Фикстура для работника с профилем"""
    EmployeeProfile.objects.create(
        user=test_employee_user,
        snils="123-456-789 01",
        organization=test_organization,
        position="Инженер",
        position_level="specialist",
    )
    return test_employee_user


@pytest.fixture
def admin_client(client, admin_user):
    """Фикстура для админ-клиента"""
    client.login(username=admin_user.username, password="admin123")
    return client


@pytest.fixture
def test_course(test_organization):
    """Фикстура курса"""
    return Course.objects.create(
        title="Тестовый курс",
        organization=test_organization,
        url="https://test.com/course",
        is_deleted=False,
    )
