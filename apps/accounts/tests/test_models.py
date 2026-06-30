import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from apps.accounts.models import (
    EmployerRegistrationRequest,
    EmployerProfile,
    EmployeeProfile,
)
from apps.organizations.models import OrganizationType

User = get_user_model()


@pytest.mark.django_db
class TestEmployerRegistrationRequestModel:
    """Тесты для модели EmployerRegistrationRequest"""

    def test_create_employer_registration_request(self, test_organization):
        """Тест создания заявки на регистрацию работодателя"""
        request = EmployerRegistrationRequest.objects.create(
            username="test_employer",
            email="employer@test.com",
            password="hashed_password",
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789012",
            status="pending",
        )

        assert request.username == "test_employer"
        assert request.email == "employer@test.com"
        assert request.short_name == "ООО Тест"
        assert request.inn == "123456789012"
        assert request.status == "pending"
        assert str(request) == "ООО Тест (На рассмотрении)"

    def test_employer_registration_request_unique_username(self, test_organization):
        """Тест уникальности username"""
        EmployerRegistrationRequest.objects.create(
            username="unique_user",
            email="unique@test.com",
            password="hash",
            short_name="Тест",
            full_name="Тестовая организация",
            inn="123456789012",
        )

        with pytest.raises(IntegrityError):
            EmployerRegistrationRequest.objects.create(
                username="unique_user",
                email="another@test.com",
                password="hash",
                short_name="Тест2",
                full_name="Тестовая организация2",
                inn="123456789013",
            )

    def test_employer_registration_request_str_method(self, test_organization):
        """Тест строкового представления"""
        request = EmployerRegistrationRequest.objects.create(
            username="test_str",
            email="str@test.com",
            password="hash",
            short_name="ООО Строк",
            full_name="Полное наименование",
            inn="123456789012",
            status="approved",
        )
        assert str(request) == "ООО Строк (Одобрено)"


@pytest.mark.django_db
class TestEmployerProfileModel:
    """Тесты для модели EmployerProfile"""

    def test_create_employer_profile(self, test_employer_user, test_organization):
        """Тест создания профиля работодателя"""
        profile = EmployerProfile.objects.create(
            user=test_employer_user,
            phone="+7 123 456-78-90",
            email="employer@company.com",
            website="https://company.com",
            contact_person_full_name="Иванов Иван Иванович",
            employee_count=100,
            annual_revenue=5000000.00,
        )

        assert profile.user == test_employer_user
        assert profile.phone == "+7 123 456-78-90"
        assert profile.email == "employer@company.com"
        assert profile.website == "https://company.com"
        assert profile.contact_person_full_name == "Иванов Иван Иванович"
        assert profile.employee_count == 100
        assert profile.annual_revenue == 5000000.00
        assert str(profile) == f"Профиль {test_organization.short_name}"

    def test_employer_profile_one_to_one_user(
        self, test_employer_user, test_organization
    ):
        """Тест уникальности связи с пользователем"""
        EmployerProfile.objects.create(user=test_employer_user)

        with pytest.raises(IntegrityError):
            EmployerProfile.objects.create(user=test_employer_user)

    def test_employer_profile_blank_fields(self, test_employer_user):
        """Тест пустых полей"""
        profile = EmployerProfile.objects.create(user=test_employer_user)

        assert profile.phone is None
        assert profile.email is None
        assert profile.website is None
        assert profile.contact_person_full_name is None
        assert profile.employee_count is None
        assert profile.annual_revenue is None

    def test_employer_profile_for_university(
        self, test_university_user, test_organization
    ):
        """Тест профиля для ВУЗа"""
        profile = EmployerProfile.objects.create(
            user=test_university_user,
            license_link="https://obrnadzor.gov.ru/license",
            dpo_programs_link="https://university.ru/dpo",
        )

        assert profile.license_link == "https://obrnadzor.gov.ru/license"
        assert profile.dpo_programs_link == "https://university.ru/dpo"


@pytest.mark.django_db
class TestEmployeeProfileModel:
    """Тесты для модели EmployeeProfile"""

    def test_create_employee_profile(
        self, test_employee_user, test_organization, test_organization_type
    ):
        """Тест создания профиля работника со всеми полями"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер-программист",
            position_level="specialist",
            phone="+7 999 123-45-67",
            gender="M",
            citizenship="Россия",
            employment_status="employed",
            work_experience_years=5,
            education_level="higher",
            education_institution="ВГУ",
            graduation_year=2015,
            specialty="Программная инженерия",
            # Новые поля
            desired_organization_type=test_organization_type,
            desired_organization="ООО ТехноИнновации",
            desired_position="Руководитель IT-отдела",
        )

        assert profile.user == test_employee_user
        assert profile.snils == "123-456-789 01"
        assert profile.organization == test_organization
        assert profile.position == "Инженер-программист"
        assert profile.position_level == "specialist"
        assert profile.phone == "+7 999 123-45-67"
        assert profile.gender == "M"
        assert profile.employment_status == "employed"
        assert profile.work_experience_years == 5
        assert profile.education_level == "higher"
        assert profile.desired_organization_type == test_organization_type
        assert profile.desired_organization == "ООО ТехноИнновации"
        assert profile.desired_position == "Руководитель IT-отдела"
        assert (
            str(profile)
            == f"{test_employee_user.get_full_name()} - {test_organization.short_name}"
        )

    def test_employee_profile_desired_fields_optional(
        self, test_employee_user, test_organization
    ):
        """Тест новых полей - все опциональны"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Тест",
            position_level="specialist",
        )

        assert profile.desired_organization_type is None
        assert profile.desired_organization is None
        assert profile.desired_position is None

    def test_employee_profile_desired_organization_type_null(
        self, test_employee_user, test_organization
    ):
        """Тест поля desired_organization_type может быть null"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Тест",
            position_level="specialist",
            desired_organization_type=None,
        )
        assert profile.desired_organization_type is None

    def test_employee_profile_unique_snils(
        self, test_employee_user, test_employee_user2, test_organization
    ):
        """Тест уникальности СНИЛС"""
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="111-222-333 44",
            organization=test_organization,
            position="Тест",
            position_level="specialist",
        )

        with pytest.raises(IntegrityError):
            EmployeeProfile.objects.create(
                user=test_employee_user2,
                snils="111-222-333 44",
                organization=test_organization,
                position="Тест2",
                position_level="specialist",
            )

    def test_employee_profile_one_to_one_user(
        self, test_employee_user, test_organization
    ):
        """Тест уникальности связи с пользователем"""
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="111-222-333 44",
            organization=test_organization,
            position="Тест",
            position_level="specialist",
        )

        with pytest.raises(IntegrityError):
            EmployeeProfile.objects.create(
                user=test_employee_user,
                snils="555-666-777 88",
                organization=test_organization,
                position="Тест2",
                position_level="specialist",
            )

    def test_employee_profile_position_level_choices(self, test_organization):
        """Тест выбора категории должности"""
        for i, (level, display) in enumerate(EmployeeProfile.POSITION_LEVEL_CHOICES):
            user = User.objects.create_user(
                username=f"test_user_{level}_{i}",
                email=f"test_{level}_{i}@test.com",
                password="testpass123",
                user_type="employee",
                last_name=f"Тестов{i}",
                first_name=f"Пользователь{i}",
            )
            snils = f"111-222-333 {i:02d}"
            profile = EmployeeProfile.objects.create(
                user=user,
                snils=snils,
                organization=test_organization,
                position="Тест",
                position_level=level,
            )
            assert profile.position_level == level
            assert profile.get_position_level_display() == display

    def test_employee_profile_gender_choices(
        self, test_employee_user, test_organization
    ):
        """Тест выбора пола"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Тест",
            position_level="specialist",
            gender="M",
        )
        assert profile.gender == "M"
        assert profile.get_gender_display() == "Мужской"

    def test_employee_profile_employment_status_choices(self, test_organization):
        """Тест выбора статуса занятости"""
        status_map = {
            "employed": "Работаю по найму",
            "self_employed": "Самозанятый",
            "entrepreneur": "ИП",
            "unemployed": "Безработный",
        }

        for i, (status, display) in enumerate(status_map.items()):
            user = User.objects.create_user(
                username=f"test_status_{status}_{i}",
                email=f"test_{status}_{i}@test.com",
                password="testpass123",
                user_type="employee",
                last_name=f"Тестов{i}",
                first_name=f"Статус{i}",
            )
            snils = f"222-333-444 {i:02d}"
            profile = EmployeeProfile.objects.create(
                user=user,
                snils=snils,
                organization=test_organization,
                position="Тест",
                position_level="specialist",
                employment_status=status,
            )
            assert profile.employment_status == status
            assert profile.get_employment_status_display() == display

    def test_employee_profile_education_level_choices(self, test_organization):
        """Тест выбора уровня образования"""
        for i, (level, display) in enumerate(EmployeeProfile.EDUCATION_LEVEL_CHOICES):
            user = User.objects.create_user(
                username=f"test_edu_{level}_{i}",
                email=f"test_edu_{level}_{i}@test.com",
                password="testpass123",
                user_type="employee",
                last_name=f"Тестов{i}",
                first_name=f"Образование{i}",
            )
            snils = f"333-444-555 {i:02d}"
            profile = EmployeeProfile.objects.create(
                user=user,
                snils=snils,
                organization=test_organization,
                position="Тест",
                position_level="specialist",
                education_level=level,
            )
            assert profile.education_level == level
            assert profile.get_education_level_display() == display
