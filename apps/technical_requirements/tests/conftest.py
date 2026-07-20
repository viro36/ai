import pytest
from django.contrib.auth import get_user_model

from apps.organizations.models import Organization, OrganizationType, District
from apps.technical_requirements.models import Question, TechnicalRequirement

User = get_user_model()


@pytest.fixture
def district():
    """Фикстура района"""
    return District.objects.create(full_name="Центральный район", short_name="ЦАО")


@pytest.fixture
def organization_type():
    """Фикстура типа организации"""
    return OrganizationType.objects.create(name="ООО")


@pytest.fixture
def university_organization(district, organization_type):
    """Фикстура организации-ВУЗа"""
    return Organization.objects.create(
        inn="123456789012",
        kpp="123456789",
        ogrn="123456789012345",
        full_name="Воронежский государственный университет",
        short_name="ВГУ",
        organization_type=organization_type,
        district=district,
        address_raw="г. Воронеж, ул. Университетская, д. 1",
        status="ACTIVE",
    )


@pytest.fixture
def employer_organization(district, organization_type):
    """Фикстура организации-работодателя"""
    return Organization.objects.create(
        inn="987654321098",
        kpp="987654321",
        ogrn="987654321098765",
        full_name="ООО Тестовая компания",
        short_name="ООО Тест",
        organization_type=organization_type,
        district=district,
        address_raw="г. Воронеж, ул. Тестовая, д. 1",
        status="ACTIVE",
    )


@pytest.fixture
def university_user(university_organization):
    """Фикстура пользователя-ВУЗа"""
    user = User.objects.create_user(
        username="university_user",
        email="university@test.com",
        password="testpass123",
        user_type="university",
        organization=university_organization,
        last_name="Петров",
        first_name="Петр",
    )
    return user


@pytest.fixture
def employer_user(employer_organization):
    """Фикстура пользователя-работодателя"""
    user = User.objects.create_user(
        username="employer_user",
        email="employer@test.com",
        password="testpass123",
        user_type="employer",
        organization=employer_organization,
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
    )
    return user


@pytest.fixture
def another_university_user():
    """Фикстура другого пользователя-ВУЗа"""
    org = Organization.objects.create(
        inn="111111111111",
        kpp="111111111",
        ogrn="111111111111111",
        full_name="Воронежский технический университет",
        short_name="ВГТУ",
        address_raw="г. Воронеж, ул. Техническая, д. 1",
        status="ACTIVE",
    )
    user = User.objects.create_user(
        username="another_university",
        email="another@test.com",
        password="testpass123",
        user_type="university",
        organization=org,
        last_name="Сидоров",
        first_name="Сидор",
    )
    return user


@pytest.fixture
def question_text():
    """Фикстура вопроса типа text"""
    return Question.objects.create(
        order=1,
        text="Опишите вашу проблему",
        question_type="text",
        is_required=True,
        placeholder="Введите текст...",
        help_text="Помощь по вопросу",
    )


@pytest.fixture
def question_textarea():
    """Фикстура вопроса типа textarea"""
    return Question.objects.create(
        order=2,
        text="Опишите вашу цель обучения",
        question_type="textarea",
        is_required=True,
        placeholder="Введите описание...",
    )


@pytest.fixture
def question_choice():
    """Фикстура вопроса типа choice"""
    return Question.objects.create(
        order=3,
        text="Выберите ключевое слово",
        question_type="choice",
        is_required=True,
        options=["Автоматизация", "Внедрение ИИ", "Свой вариант"],
    )


@pytest.fixture
def question_multiple_choice():
    """Фикстура вопроса типа multiple_choice"""
    return Question.objects.create(
        order=4,
        text="Выберите технологии",
        question_type="multiple_choice",
        is_required=True,
        options=["Docker", "Kubernetes", "Terraform"],
    )


@pytest.fixture
def question_boolean():
    """Фикстура вопроса типа boolean"""
    return Question.objects.create(
        order=5,
        text="Необходимо ли обучение на оборудовании?",
        question_type="boolean",
        is_required=True,
    )


@pytest.fixture
def question_date():
    """Фикстура вопроса типа date"""
    return Question.objects.create(
        order=6,
        text="Укажите желаемую дату начала",
        question_type="date",
        is_required=True,
    )


@pytest.fixture
def question_number():
    """Фикстура вопроса типа number"""
    return Question.objects.create(
        order=7,
        text="Сколько человек планируете обучить?",
        question_type="number",
        is_required=True,
        placeholder="Введите количество",
    )


@pytest.fixture
def question_depends_on(question_boolean):
    """Фикстура вопроса с зависимостью"""
    return Question.objects.create(
        order=8,
        text="Желаемая площадка стажировки",
        question_type="text",
        is_required=False,
        depends_on=question_boolean,
        depends_value="True",
        placeholder="Название площадки",
    )


@pytest.fixture
def question_inactive():
    """Фикстура неактивного вопроса"""
    return Question.objects.create(
        order=9,
        text="Неактивный вопрос",
        question_type="text",
        is_active=False,
    )


@pytest.fixture
def technical_requirement(employer_user, university_user, question_text):
    """Фикстура технического задания"""
    answers = {
        str(question_text.id): "Тестовый ответ",
    }
    requirement = TechnicalRequirement.objects.create(
        employer=employer_user,
        answers=answers,
        status="sent",
    )
    requirement.universities.add(university_user.organization)
    return requirement


@pytest.fixture
def draft_requirement(employer_user, university_user):
    """Фикстура черновика технического задания"""
    requirement = TechnicalRequirement.objects.create(
        employer=employer_user,
        answers={},
        status="draft",
    )
    requirement.universities.add(university_user.organization)
    return requirement


@pytest.fixture
def admin_user():
    """Фикстура администратора"""
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="admin123",
        user_type="admin",
    )
