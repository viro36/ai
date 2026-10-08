import pytest
from apps.accounts.forms import (
    EmployerRegistrationForm,
    EmployerProfileForm,
    EmployeeRegistrationForm,
    EmployeeProfileForm,
)
from apps.accounts.models import EmployeeProfile


@pytest.mark.django_db
class TestEmployerRegistrationForm:
    """Тесты для формы регистрации работодателя"""

    def test_form_valid(self, test_organization):
        """Тест валидной формы"""
        form_data = {
            "username": "test_employer",
            "email": "employer@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123456789012",
        }
        form = EmployerRegistrationForm(data=form_data)
        assert form.is_valid()

    def test_username_exists(self, test_employer_user):
        """Тест: username уже существует"""
        form_data = {
            "username": "test_employer",
            "email": "new@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123456789099",
        }
        form = EmployerRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "username" in form.errors
        assert "уже существует" in str(form.errors["username"])

    def test_email_exists(self, test_employer_user):
        """Тест: email уже существует"""
        form_data = {
            "username": "new_user",
            "email": "employer@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123456789099",
        }
        form = EmployerRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_passwords_not_match(self):
        """Тест: пароли не совпадают"""
        form_data = {
            "username": "test_user",
            "email": "test@test.com",
            "password": "pass123",
            "password_confirm": "pass456",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123456789012",
        }
        form = EmployerRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "password_confirm" in form.errors

    def test_inn_invalid_format(self):
        """Тест: неверный формат ИНН"""
        form_data = {
            "username": "test_user",
            "email": "test@test.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123",  # Слишком короткий
        }
        form = EmployerRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "inn" in form.errors

    def test_inn_with_letters(self):
        """Тест: ИНН содержит буквы"""
        form_data = {
            "username": "test_user",
            "email": "test@test.com",
            "password": "pass123",
            "password_confirm": "pass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "abc123def",
        }
        form = EmployerRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "inn" in form.errors
        assert "только цифры" in str(form.errors["inn"])


@pytest.mark.django_db
class TestEmployeeRegistrationForm:
    """Тесты для формы регистрации работника"""

    def test_form_valid(self, test_organization):
        """Тест валидной формы"""
        form_data = {
            "username": "test_employee",
            "email": "employee@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "snils": "123-456-789 01",
            "organization": test_organization.id,
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeRegistrationForm(data=form_data)
        assert form.is_valid()

    def test_username_exists(self, test_employee_user):
        """Тест: username уже существует"""
        form_data = {
            "username": "test_employee",
            "email": "new@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "111-222-333 44",
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "username" in form.errors

    def test_email_exists(self, test_employee_user):
        """Тест: email уже существует"""
        form_data = {
            "username": "new_user",
            "email": "employee@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "111-222-333 44",
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_snils_invalid_format(self):
        """Тест: неверный формат СНИЛС"""
        form_data = {
            "username": "test_user",
            "email": "test@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "12345",
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "snils" in form.errors

    def test_passwords_not_match(self):
        """Тест: пароли не совпадают"""
        form_data = {
            "username": "test_user",
            "email": "test@test.com",
            "password": "pass123",
            "password_confirm": "pass456",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeRegistrationForm(data=form_data)
        assert not form.is_valid()
        assert "password_confirm" in form.errors


@pytest.mark.django_db
class TestEmployerProfileForm:
    """Тесты для формы профиля работодателя"""

    def test_form_valid(self, test_employer_user):
        """Тест валидной формы"""
        form_data = {
            "registration_email": "newemail@test.com",
            "phone": "+7 999 123-45-67",
            "website": "https://example.com",
            "employee_count": 100,
        }
        form = EmployerProfileForm(data=form_data)
        assert form.is_valid()

    def test_form_with_all_fields(self, test_employer_user):
        """Тест с заполнением всех полей"""
        form_data = {
            "registration_email": "company@test.com",
            "actual_address": "г. Москва, ул. Тестовая, д. 1",
            "phone": "+7 999 123-45-67",
            "email": "info@company.com",
            "website": "https://company.com",
            "contact_person_full_name": "Иванов Иван Иванович",
            "contact_person_position": "Директор",
            "contact_person_phone": "+7 999 765-43-21",
            "contact_person_email": "ivanov@company.com",
            "checking_account": "40702810123456789012",
            "bank_name": "Сбербанк",
            "bik": "044525225",
            "correspondent_account": "30101810400000000225",
            "employee_count": 150,
            "annual_revenue": 10000000.00,
        }
        form = EmployerProfileForm(data=form_data)
        assert form.is_valid()

    def test_optional_fields(self, test_employer_user):
        """Тест: необязательные поля могут быть пустыми"""
        form_data = {
            "registration_email": "email@test.com",
        }
        form = EmployerProfileForm(data=form_data)
        assert form.is_valid()


@pytest.mark.django_db
class TestEmployeeProfileForm:
    """Тесты для формы профиля работника"""

    def test_form_valid(self, test_employee_user, test_organization):
        """Тест валидной формы"""
        form_data = {
            "last_name": "Петров",
            "first_name": "Петр",
            "patronymic": "Петрович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "newemail@test.com",
            "position": "Старший инженер",
            "position_level": "specialist",
            "gender": "M",
            "citizenship": "Россия",
            "phone": "+7 999 123-45-67",
            "locality": "Москва",
            "municipality": "ЦАО",
            "employment_status": "employed",
            "work_experience_years": 10,
            "education_level": "higher",
            "education_institution": "МГУ",
            "graduation_year": 2010,
            "specialty": "Программист",
        }
        form = EmployeeProfileForm(data=form_data)
        assert form.is_valid()

    def test_optional_fields(self, test_employee_user, test_organization):
        """Тест: необязательные поля могут быть пустыми"""
        form_data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
        }
        form = EmployeeProfileForm(data=form_data)
        assert form.is_valid()

    def test_gender_choices(self, test_employee_user, test_organization):
        """Тест выбора пола"""
        form_data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
            "gender": "M",
        }
        form = EmployeeProfileForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["gender"] == "M"

    def test_employment_status_choices(self, test_employee_user, test_organization):
        """Тест выбора статуса занятости"""
        form_data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
            "employment_status": "employed",
        }
        form = EmployeeProfileForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["employment_status"] == "employed"

    def test_education_level_choices(self, test_employee_user, test_organization):
        """Тест выбора уровня образования"""
        form_data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
            "education_level": "higher",
        }
        form = EmployeeProfileForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["education_level"] == "higher"


@pytest.mark.django_db
class TestEmployeeRegistrationFormUnemployed:
    """Тесты формы регистрации безработного"""

    def _base_data(self, **overrides):
        """Базовые данные формы"""
        data = {
            "username": "unemployed_user",
            "email": "unemployed@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
        }
        data.update(overrides)
        return data

    def test_valid_unemployed(self):
        """Безработный: organization/position/position_level не нужны"""
        form = EmployeeRegistrationForm(data=self._base_data(is_unemployed=True))
        assert form.is_valid(), form.errors
        assert form.cleaned_data["organization"] is None
        assert form.cleaned_data["position"] == "Безработный"
        assert form.cleaned_data["position_level"] is None

    def test_valid_unemployed_svo(self):
        """Безработный + СВО"""
        form = EmployeeRegistrationForm(
            data=self._base_data(
                username="unemployed_svo",
                email="unemployed_svo@test.com",
                is_unemployed=True,
                is_svo_participant=True,
            )
        )
        assert form.is_valid(), form.errors

    def test_valid_working_svo(self, test_organization):
        """Работающий + СВО (СВО независим от безработного)"""
        form = EmployeeRegistrationForm(
            data=self._base_data(
                username="working_svo",
                email="working_svo@test.com",
                organization=test_organization.id,
                position="Инженер",
                position_level="specialist",
                is_svo_participant=True,
            )
        )
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestEmployeeRegistrationFormSave:
    """Сохранение формы регистрации"""

    def _base_data(self, **overrides):
        data = {
            "username": "save_user",
            "email": "save@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
        }
        data.update(overrides)
        return data

    def test_save_unemployed(self):
        """save(): безработный - organization=None, position='Безработный'"""
        form = EmployeeRegistrationForm(
            data=self._base_data(
                username="save_unemployed",
                email="save_unemployed@test.com",
                is_unemployed=True,
            )
        )
        assert form.is_valid(), form.errors

        profile = form.save(commit=False)
        assert profile.organization is None
        assert profile.position == "Безработный"
        assert profile.position_level is None
        assert profile.is_unemployed is True
        assert profile.is_svo_participant is False

    def test_save_unemployed_svo(self):
        """save(): безработный + СВО"""
        form = EmployeeRegistrationForm(
            data=self._base_data(
                username="save_unemployed_svo",
                email="save_unemployed_svo@test.com",
                is_unemployed=True,
                is_svo_participant=True,
            )
        )
        assert form.is_valid(), form.errors

        profile = form.save(commit=False)
        assert profile.organization is None
        assert profile.is_unemployed is True
        assert profile.is_svo_participant is True

    def test_save_working_svo(self, test_organization):
        """save(): работающий + СВО - реальная организация + флаг"""
        form = EmployeeRegistrationForm(
            data=self._base_data(
                username="save_working_svo",
                email="save_working_svo@test.com",
                organization=test_organization.id,
                position="Инженер",
                position_level="specialist",
                is_svo_participant=True,
            )
        )
        assert form.is_valid(), form.errors

        profile = form.save(commit=False)
        assert profile.organization == test_organization
        assert profile.position == "Инженер"
        assert profile.position_level == "specialist"
        assert profile.is_unemployed is False
        assert profile.is_svo_participant is True


@pytest.mark.django_db
class TestEmployeeProfileFormUnemployed:
    """Тесты формы профиля работника"""

    def _base_data(self, **overrides):
        data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
        }
        data.update(overrides)
        return data

    def _make_profile(self, test_employee_user, test_organization, **kwargs):
        defaults = {
            "snils": "123-456-789 01",
            "organization": test_organization,
            "position": "Инженер",
            "position_level": "specialist",
        }
        defaults.update(kwargs)
        return EmployeeProfile.objects.create(user=test_employee_user, **defaults)

    def test_save_unemployed_sets_defaults(self, test_employee_user, test_organization):
        """save(): безработный - organization=None, position='Безработный'"""
        profile = self._make_profile(test_employee_user, test_organization)
        form = EmployeeProfileForm(
            data=self._base_data(is_unemployed=True),
            instance=profile,
        )
        assert form.is_valid(), form.errors

        saved = form.save(commit=False)
        assert saved.organization is None
        assert saved.position == "Безработный"
        assert saved.position_level is None
        assert saved.is_unemployed is True

    def test_save_working_restores_fields(self, test_employee_user, test_organization):
        """save(): снятие галочки - восстановление position и position_level"""
        profile = self._make_profile(
            test_employee_user,
            test_organization,
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )
        form = EmployeeProfileForm(
            data=self._base_data(organization=test_organization.id),
            instance=profile,
        )
        assert form.is_valid(), form.errors

        saved = form.save(commit=False)
        assert saved.position == "Инженер"
        assert saved.position_level == "specialist"
        assert saved.is_unemployed is False


@pytest.mark.django_db
class TestEmployeeRegistrationFormPosition:
    """Проверка обязательности position для работающих"""

    def _base(self, **overrides):
        data = {
            "username": "pos_user",
            "email": "pos@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "123-456-789 01",
        }
        data.update(overrides)
        return data

    def test_position_required_for_employed(self, test_organization):
        """Работающий без должности → ошибка"""
        form = EmployeeRegistrationForm(
            data=self._base(
                organization=test_organization.id,
                position="",
                position_level="specialist",
            )
        )
        assert not form.is_valid()
        assert "position" in form.errors

    def test_unemployed_sets_default_position(self):
        """Безработный: position='Безработный'"""
        form = EmployeeRegistrationForm(
            data=self._base(
                is_unemployed=True,
                position="",
                position_level="",
            )
        )
        assert form.is_valid(), form.errors
        profile = form.save(commit=False)
        assert profile.position == "Безработный"
        assert profile.position_level is None
        assert profile.organization is None
