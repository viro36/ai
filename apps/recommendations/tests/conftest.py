import pytest
from datetime import datetime, timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage

from apps.courses.models import Course, Category
from apps.organizations.models import Organization
from apps.surveys.models import SurveyCategory
from apps.recommendations.models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
    RecommendationTask,
    SelectedCourse,
)
from apps.accounts.models import EmployeeProfile

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
def course_with_start_date_future(organization):
    """Фикстура курса с датой начала в будущем"""
    future_date = (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y")
    return Course.objects.create(
        title="Курс с датой в будущем",
        organization=organization,
        url="https://example.com/course/future",
        start_dates=future_date,
        is_deleted=False,
    )


@pytest.fixture
def course_with_start_date_past(organization):
    """Фикстура курса с датой начала в прошлом"""
    past_date = (datetime.now() - timedelta(days=30)).strftime("%d.%m.%Y")
    return Course.objects.create(
        title="Курс с датой в прошлом",
        organization=organization,
        url="https://example.com/course/past",
        start_dates=past_date,
        is_deleted=False,
    )


@pytest.fixture
def course_with_start_date_text(organization):
    """Фикстура курса с текстовой датой начала"""
    return Course.objects.create(
        title="Курс с текстовой датой",
        organization=organization,
        url="https://example.com/course/text",
        start_dates="сентябрь 2026",
        is_deleted=False,
    )


@pytest.fixture
def course_without_start_date(organization):
    """Фикстура курса без даты начала"""
    return Course.objects.create(
        title="Курс без даты начала",
        organization=organization,
        url="https://example.com/course/no_date",
        start_dates="",
        is_deleted=False,
    )


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
    user = User.objects.create_user(
        username="regular_user",
        email="user@example.com",
        password="testpass123",
        user_type="regular",
    )
    return user


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


# ========== ФИКСТУРЫ ДЛЯ РЕКОМЕНДАЦИЙ ==========


@pytest.fixture
def survey_category():
    """Фикстура категории опроса"""
    return SurveyCategory.objects.create(
        name="RIASEC",
        description="Опросник профессиональных склонностей",
        is_active=True,
    )


@pytest.fixture
def survey_session(regular_user, survey_category):
    """Фикстура сессии опроса"""
    from apps.surveys.models import SurveySession as Session

    return Session.objects.create(
        user=regular_user,
        category=survey_category,
        status="completed",
        completed_at=timezone.now(),
    )


@pytest.fixture
def course_recommendation(regular_user, course):
    """Фикстура рекомендации курса"""
    return CourseRecommendation.objects.create(
        user=regular_user,
        course=course,
        reason="Тестовая рекомендация",
        relevance_score=0.85,
        order=1,
    )


@pytest.fixture
def course_recommendations(regular_user, multiple_courses):
    """Фикстура нескольких рекомендаций"""
    recommendations = []
    for i, course in enumerate(multiple_courses[:5]):
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason=f"Рекомендация {i+1}",
            relevance_score=0.9 - (i * 0.1),
            order=i,
        )
        recommendations.append(rec)
    return recommendations


@pytest.fixture
def recommendation_task(regular_user):
    """Фикстура задачи рекомендаций"""
    return RecommendationTask.objects.create(
        user=regular_user,
        task_id="test-task-123",
        status="pending",
    )


@pytest.fixture
def user_with_employee_profile(regular_user, organization):
    """Фикстура пользователя с профилем работника"""
    profile = EmployeeProfile.objects.create(
        user=regular_user,
        position="Начальник цеха",
        position_level="middle",
        organization=organization,
    )
    return regular_user


@pytest.fixture
def survey_category():
    """Фикстура категории опроса"""
    return SurveyCategory.objects.create(
        name="RIASEC",
        description="Опросник профессиональных склонностей",
        is_active=True,
    )


@pytest.fixture
def survey_session(regular_user, survey_category):
    """Фикстура сессии опроса"""
    from apps.surveys.models import SurveySession as Session

    return Session.objects.create(
        user=regular_user,
        category=survey_category,
        status="completed",
        completed_at=timezone.now(),
    )


@pytest.fixture
def course_recommendation(regular_user, course):
    """Фикстура рекомендации курса"""
    return CourseRecommendation.objects.create(
        user=regular_user,
        course=course,
        reason="Тестовая рекомендация",
        relevance_score=0.85,
        order=1,
    )


@pytest.fixture
def course_recommendations(regular_user, multiple_courses):
    """Фикстура нескольких рекомендаций"""
    recommendations = []
    for i, course in enumerate(multiple_courses[:5]):
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=course,
            reason=f"Рекомендация {i+1}",
            relevance_score=0.9 - (i * 0.1),
            order=i,
        )
        recommendations.append(rec)
    return recommendations


@pytest.fixture
def recommendation_task(regular_user):
    """Фикстура задачи рекомендаций"""
    return RecommendationTask.objects.create(
        user=regular_user,
        task_id="test-task-123",
        status="pending",
    )


@pytest.fixture
def selected_course(regular_user, course):
    """Фикстура выбранного курса"""
    return SelectedCourse.objects.create(
        user=regular_user,
        course=course,
    )


@pytest.fixture
def user_with_employee_profile(regular_user, organization):
    """Фикстура пользователя с профилем работника"""
    profile = EmployeeProfile.objects.create(
        user=regular_user,
        position="Начальник цеха",
        position_level="middle",
        organization=organization,
    )
    return regular_user


@pytest.fixture
def viewer_user():
    """Фикстура пользователя-просмотрщика с правами на просмотр в recommendations"""
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

    group, _ = Group.objects.get_or_create(name="Просмотрщик")
    user.groups.add(group)

    for model in [
        CourseRecommendation,
        RecommendationTask,
        SelectedCourse,
        ApprovedSelectedCourse,
        EmployerRecommendation,
    ]:
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


@pytest.fixture
def admin_client(client, admin_user):
    """Фикстура для клиента администратора"""
    client.login(username=admin_user.username, password="adminpass123")
    return client


@pytest.fixture
def test_question_choice():
    """Фикстура вопроса типа choice"""
    from apps.goal_setting.models import Question, QuestionOption

    question = Question.objects.create(
        text="Какой ваш любимый язык программирования?",
        question_type="choice",
        is_active=True,
        order=1,
    )
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
    return question


@pytest.fixture
def test_question_text():
    """Фикстура вопроса типа text"""
    from apps.goal_setting.models import Question

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
    from apps.goal_setting.models import Question, QuestionOption

    question = Question.objects.create(
        text="Какие технологии вы используете?",
        question_type="multiple_choice",
        is_active=True,
        order=3,
        is_multiple=True,
    )
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
    return question


@pytest.fixture
def test_question_date_range():
    """Фикстура вопроса типа date_range"""
    from apps.goal_setting.models import Question

    return Question.objects.create(
        text="Укажите период вашей работы на последнем месте",
        question_type="date_range",
        is_active=True,
        order=4,
    )


@pytest.fixture
def test_question_inactive():
    """Фикстура неактивного вопроса"""
    from apps.goal_setting.models import Question

    return Question.objects.create(
        text="Неактивный вопрос",
        question_type="text",
        is_active=False,
        order=999,
    )


@pytest.fixture
def test_employer_user(organization):
    """Фикстура для пользователя-работодателя"""
    user = User.objects.create_user(
        username="test_employer",
        email="employer@test.com",
        password="testpass123",
        user_type="employer",
        organization=organization,
        last_name="Иванов",
        first_name="Иван",
    )
    return user


@pytest.fixture
def employer_user(organization):
    """Фикстура для пользователя-работодателя (для тестов моделей)"""
    user = User.objects.create_user(
        username="employer_user",
        email="employer_user@test.com",
        password="testpass123",
        user_type="employer",
        organization=organization,
        last_name="Петров",
        first_name="Петр",
    )
    return user


@pytest.fixture
def test_employee_user(organization):
    """Фикстура для пользователя-работника"""
    user = User.objects.create_user(
        username="test_employee",
        email="employee@test.com",
        password="testpass123",
        user_type="employee",
        organization=organization,
        last_name="Иванов",
        first_name="Иван",
        patronymic="Иванович",
        snils="123-456-789 01",
    )
    # Создаём профиль работника
    EmployeeProfile.objects.create(
        user=user,
        snils="123-456-789 01",
        organization=organization,
        position="Начальник цеха",
        position_level="middle",
    )
    return user


@pytest.fixture
def employer_recommendation(test_employer_user, test_employee_user, course):
    """Фикстура рекомендации от работодателя"""
    from apps.recommendations.models import EmployerRecommendation

    return EmployerRecommendation.objects.create(
        employer=test_employer_user,
        employee=test_employee_user,
        course=course,
        reason="Тестовая рекомендация",
    )


@pytest.fixture
def test_employee_user2(organization):
    """Фикстура для второго пользователя-работника"""
    user = User.objects.create_user(
        username="test_employee2",
        email="employee2@test.com",
        password="testpass123",
        user_type="employee",
        organization=organization,
        last_name="Петров",
        first_name="Петр",
        patronymic="Петрович",
        snils="987-654-321 01",
    )
    return user
