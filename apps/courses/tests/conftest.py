import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.courses.models import Course, Category
from apps.organizations.models import Organization

User = get_user_model()


@pytest.fixture
def organization():
    """Фикстура организации (ВУЗа)"""
    return Organization.objects.create(
        inn="1234567890",
        short_name="ВГУ",
        full_name="Воронежский государственный университет",
        status="ACTIVE",
    )


@pytest.fixture
def another_organization():
    """Фикстура другой организации"""
    return Organization.objects.create(
        inn="0987654321",
        short_name="ВГТУ",
        full_name="Воронежский государственный технический университет",
        status="ACTIVE",
    )


@pytest.fixture
def category():
    """Фикстура категории"""
    return Category.objects.create(name="Искусственный интеллект")


@pytest.fixture
def another_category():
    """Фикстура другой категории"""
    return Category.objects.create(name="Машинное обучение")


@pytest.fixture
def third_category():
    """Фикстура третьей категории"""
    return Category.objects.create(name="Информационные технологии")


@pytest.fixture
def category_with_long_name():
    """Фикстура категории с длинным названием"""
    return Category.objects.create(
        name="Сквозные виды профессиональной деятельности в промышленности"
    )


@pytest.fixture
def course(organization, category):
    """Фикстура курса"""
    course = Course.objects.create(
        title="Python для анализа данных",
        description="Курс по анализу данных на Python",
        organization=organization,
        url="https://example.com/course/1",
        program_type="Профессиональная переподготовка",
        duration_hours=72,
        duration_weeks="12 недель",
        study_mode="Очно-заочная",
        format="Онлайн",
        teachers="Иванов И.И.",
        target_audience="Начинающие разработчики",
        topics="Python, Pandas, NumPy",
        start_dates="01.09.2024",
        price="35000",
        field_of_study="01.03.02 Прикладная математика и информатика",
        document_type="Диплом о профессиональной переподготовке",
        is_deleted=False,
    )
    course.categories.add(category)
    return course


@pytest.fixture
def course_with_multiple_categories(
    organization, category, another_category, third_category
):
    """Фикстура курса с несколькими категориями"""
    course = Course.objects.create(
        title="Курс с несколькими категориями",
        description="Тестовый курс с множеством категорий",
        organization=organization,
        url="https://example.com/course/multiple",
        is_deleted=False,
    )
    course.categories.add(category, another_category, third_category)
    return course


@pytest.fixture
def course_with_many_categories(organization):
    """Фикстура курса с большим количеством категорий (>5)"""
    course = Course.objects.create(
        title="Курс с многими категориями",
        organization=organization,
        url="https://example.com/course/many",
        is_deleted=False,
    )
    names = [
        "Категория 1",
        "Категория 2",
        "Категория 3",
        "Категория 4",
        "Категория 5",
        "Категория 6",
        "Категория 7",
    ]
    for name in names:
        cat, _ = Category.objects.get_or_create(name=name)
        course.categories.add(cat)
    return course


@pytest.fixture
def deleted_course(organization):
    """Фикстура удалённого курса"""
    return Course.objects.create(
        title="Удалённый курс",
        description="Этот курс удалён",
        organization=organization,
        url="https://example.com/course/deleted",
        is_deleted=True,
        deleted_at=timezone.now(),
    )


@pytest.fixture
def university_admin_user(organization):
    """Фикстура пользователя - админ ВУЗа"""
    user = User.objects.create_user(
        username="university_admin",
        email="admin@vsu.ru",
        password="testpass123",
        user_type="university",
    )
    user.organization = organization
    user.save()
    return user


@pytest.fixture
def regular_user():
    """Фикстура обычного пользователя"""
    return User.objects.create_user(
        username="regular_user",
        email="user@example.com",
        password="testpass123",
        user_type="regular",
    )


@pytest.fixture
def admin_user():
    """Фикстура суперпользователя"""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        user_type="admin",
    )


@pytest.fixture
def multiple_courses(organization):
    """Фикстура нескольких курсов для тестирования пагинации и фильтрации"""
    courses = []
    for i in range(15):
        course = Course.objects.create(
            title=f"Курс {i}",
            organization=organization,
            url=f"https://example.com/course/{i}",
            is_deleted=False,
        )
        courses.append(course)
    return courses


@pytest.fixture
def course_with_all_fields(organization):
    """Фикстура курса со всеми заполненными полями"""
    return Course.objects.create(
        title="Полный курс со всеми полями",
        description="Полное описание курса с деталями",
        organization=organization,
        program_type="Повышение квалификации",
        duration_hours=120,
        duration_weeks="16 недель",
        study_mode="Заочная",
        format="Офлайн",
        teachers="Петров П.П., Сидоров С.С.",
        target_audience="Специалисты с высшим образованием",
        topics="Модуль 1, Модуль 2, Модуль 3",
        start_dates="01.10.2024, 01.02.2025",
        price="50000",
        field_of_study="09.03.01 Информатика и вычислительная техника",
        document_type="Удостоверение о повышении квалификации",
        url="https://example.com/course/full",
        last_parsed=timezone.now(),
        is_deleted=False,
    )


@pytest.fixture
def request_factory():
    """Фикстура фабрики запросов"""
    return RequestFactory()


@pytest.fixture
def mock_request_with_messages(request_factory):
    """Фикстура запроса с messages"""
    req = request_factory.get("/")
    req.user = None
    setattr(req, "session", "session")
    messages = FallbackStorage(req)
    setattr(req, "_messages", messages)
    return req


@pytest.fixture
def authenticated_university_user(university_admin_user, organization):
    """Фикстура авторизованного пользователя ВУЗа"""
    user = university_admin_user
    user.organization = organization
    user.save()
    return user


@pytest.fixture
def course_data(organization):
    """Фикстура данных для создания курса"""
    return {
        "title": "Новый тестовый курс",
        "description": "Описание тестового курса",
        "url": "https://example.com/course/new",
        "program_type": "Профессиональная переподготовка",
        "duration_hours": 72,
        "duration_weeks": "12 недель",
        "study_mode": "Очно-заочная",
        "format": "Онлайн",
        "teachers": "Тестовый преподаватель",
        "target_audience": "Тестовая аудитория",
        "topics": "Тема 1, Тема 2",
        "start_dates": "01.09.2024",
        "price": "35000",
        "field_of_study": "01.03.02 Прикладная математика",
        "document_type": "Диплом",
    }


@pytest.fixture
def course_update_data():
    """Фикстура данных для обновления курса"""
    return {
        "title": "Обновлённый курс",
        "description": "Обновлённое описание",
        "url": "https://example.com/course/updated",
        "program_type": "Повышение квалификации",
        "duration_hours": 120,
        "duration_weeks": "16 недель",
        "price": "50000",
    }


@pytest.fixture
def viewer_user():
    """Фикстура пользователя-просмотрщика с правами на просмотр курсов"""
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

    # Даем права на просмотр курсов и категорий
    for model in [Course, Category]:
        ct = ContentType.objects.get_for_model(model)
        # Права на просмотр
        view_perm, _ = Permission.objects.get_or_create(
            content_type=ct,
            codename=f"view_{model._meta.model_name}",
            defaults={"name": f"Can view {model._meta.model_name}"},
        )
        group.permissions.add(view_perm)

    return user


@pytest.fixture
def viewer_user_no_perms():
    """Фикстура пользователя-просмотрщика без прав (для проверки запрета)"""
    user = User.objects.create_user(
        username="viewer_no_perms",
        email="viewer_no_perms@test.com",
        password="viewer123",
        user_type="admin",
        is_staff=True,
        is_active=True,
        first_name="Просмотр",
        last_name="Безправов",
    )

    group, _ = Group.objects.get_or_create(name="Просмотрщик")
    user.groups.add(group)
    # Не даем никаких прав
    return user
