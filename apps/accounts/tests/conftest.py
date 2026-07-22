import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import (
    EmployeeProfile,
    EmployerProfile,
    EmployerRegistrationRequest,
)
from apps.courses.models import Course
from apps.organizations.models import Organization, District, OrganizationType
from apps.goal_setting.models import Question, QuestionOption
from apps.recommendations.models import CourseRecommendation, SelectedCourse

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


@pytest.fixture
def test_question_choice():
    """Фикстура вопроса типа choice"""
    question = Question.objects.create(
        text="Какой ваш любимый язык программирования?",
        question_type="choice",
        is_active=True,
        order=1,
    )
    # Создаём варианты ответов
    QuestionOption.objects.create(
        question=question,
        value="python",
        label="Python",
        order=1,
    )
    QuestionOption.objects.create(
        question=question,
        value="javascript",
        label="JavaScript",
        order=2,
    )
    QuestionOption.objects.create(
        question=question,
        value="java",
        label="Java",
        order=3,
    )
    return question


@pytest.fixture
def test_question_text():
    """Фикстура вопроса типа text"""
    return Question.objects.create(
        text="Опишите ваш опыт работы",
        question_type="text",
        is_active=True,
        order=2,
        max_length=1000,
    )


@pytest.fixture
def test_question_multiple_choice():
    """Фикстура вопроса типа multiple_choice"""
    question = Question.objects.create(
        text="Какие технологии вы используете?",
        question_type="multiple_choice",
        is_active=True,
        order=3,
        is_multiple=True,
    )
    # Создаём варианты ответов
    QuestionOption.objects.create(
        question=question,
        value="docker",
        label="Docker",
        order=1,
    )
    QuestionOption.objects.create(
        question=question,
        value="kubernetes",
        label="Kubernetes",
        order=2,
    )
    QuestionOption.objects.create(
        question=question,
        value="terraform",
        label="Terraform",
        order=3,
    )
    return question


@pytest.fixture
def test_question_date_range():
    """Фикстура вопроса типа date_range"""
    return Question.objects.create(
        text="Укажите период вашей работы на последнем месте",
        question_type="date_range",
        is_active=True,
        order=4,
    )


@pytest.fixture
def test_question_inactive():
    """Фикстура неактивного вопроса"""
    return Question.objects.create(
        text="Неактивный вопрос",
        question_type="text",
        is_active=False,
        order=999,
    )


@pytest.fixture
def test_employee_user_with_selected_courses(test_employee_user, test_organization):
    """Фикстура для работника с выбранными курсами"""
    courses = []
    for i in range(3):
        course = Course.objects.create(
            title=f"Выбранный курс {i}",
            organization=test_organization,
            url=f"https://test.com/selected{i}",
            is_deleted=False,
        )
        SelectedCourse.objects.create(
            user=test_employee_user,
            course=course,
        )
        courses.append(course)
    return test_employee_user


@pytest.fixture
def test_employee_user_with_recommendations(test_employee_user, test_course):
    """Фикстура для работника с рекомендациями"""
    for i in range(5):
        CourseRecommendation.objects.create(
            user=test_employee_user,
            course=test_course,
            reason=f"Тестовая причина {i}",
            relevance_score=0.8,
            order=i,
        )
    return test_employee_user


@pytest.fixture
def viewer_user(db):
    """Фикстура пользователя-просмотрщика с правами на просмотр в accounts"""
    user = User.objects.create_user(
        username="viewer",
        email="viewer@test.com",
        password="viewer123",
        user_type="admin",
        is_staff=True,
        is_active=True,
        first_name="Просмотр",
        last_name="Просмотрщиков",
    )

    # Создаем группу
    group, _ = Group.objects.get_or_create(name="Просмотрщик")
    user.groups.add(group)

    # Даем права на просмотр моделей accounts
    for model in [EmployerRegistrationRequest, EmployerProfile, EmployeeProfile]:
        ct = ContentType.objects.get_for_model(model)
        view_perm, _ = Permission.objects.get_or_create(
            content_type=ct,
            codename=f"view_{model._meta.model_name}",
            defaults={"name": f"Can view {model._meta.model_name}"},
        )
        group.permissions.add(view_perm)

    return user


@pytest.fixture
def viewer_client(client, viewer_user):
    """Фикстура для клиента просмотрщика"""
    client.login(username=viewer_user.username, password="viewer123")
    return client
