import pytest
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone

from apps.accounts.models import EmployeeProfile
from apps.courses.models import Course, Category
from apps.organizations.models import Organization
from apps.recommendations.models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
    RecommendationTask,
    SelectedCourse,
)
from apps.surveys.models import SurveyCategory

User = get_user_model()


# ============================================================
# Организации
# ============================================================
@pytest.fixture
def organization():
    return Organization.objects.create(
        inn="1234567890",
        short_name="ВГУ",
        full_name="Воронежский государственный университет",
        status="ACTIVE",
    )


@pytest.fixture
def another_organization():
    return Organization.objects.create(
        inn="0987654321",
        short_name="ВГТУ",
        full_name="Воронежский государственный технический университет",
        status="ACTIVE",
    )


# ============================================================
# Категории
# ============================================================
@pytest.fixture
def category():
    return Category.objects.create(name="Искусственный интеллект")


@pytest.fixture
def another_category():
    return Category.objects.create(name="Машинное обучение")


@pytest.fixture
def third_category():
    return Category.objects.create(name="Информационные технологии")


@pytest.fixture
def category_with_long_name():
    return Category.objects.create(
        name="Сквозные виды профессиональной деятельности в промышленности"
    )


# ============================================================
# Курсы
# ============================================================
@pytest.fixture
def course(organization, category):
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
def another_course(organization, another_category):
    course = Course.objects.create(
        title="Машинное обучение на практике",
        organization=organization,
        url="https://example.com/course/2",
        is_deleted=False,
    )
    course.categories.add(another_category)
    return course


@pytest.fixture
def course_with_multiple_categories(
    organization, category, another_category, third_category
):
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
    course = Course.objects.create(
        title="Курс с многими категориями",
        organization=organization,
        url="https://example.com/course/many",
        is_deleted=False,
    )
    names = [f"Категория {i}" for i in range(1, 8)]
    for name in names:
        cat, _ = Category.objects.get_or_create(name=name)
        course.categories.add(cat)
    return course


@pytest.fixture
def course_with_start_date_future(organization):
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
    return Course.objects.create(
        title="Курс с текстовой датой",
        organization=organization,
        url="https://example.com/course/text",
        start_dates="сентябрь 2026",
        is_deleted=False,
    )


@pytest.fixture
def course_without_start_date(organization):
    return Course.objects.create(
        title="Курс без даты начала",
        organization=organization,
        url="https://example.com/course/no_date",
        start_dates="",
        is_deleted=False,
    )


@pytest.fixture
def deleted_course(organization):
    return Course.objects.create(
        title="Удалённый курс",
        description="Этот курс удалён",
        organization=organization,
        url="https://example.com/course/deleted",
        is_deleted=True,
        deleted_at=timezone.now(),
    )


@pytest.fixture
def multiple_courses(organization):
    return [
        Course.objects.create(
            title=f"Курс {i}",
            organization=organization,
            url=f"https://example.com/course/{i}",
            is_deleted=False,
        )
        for i in range(15)
    ]


@pytest.fixture
def course_with_all_fields(organization):
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
def course_data(organization):
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
    return {
        "title": "Обновлённый курс",
        "description": "Обновлённое описание",
        "url": "https://example.com/course/updated",
        "program_type": "Повышение квалификации",
        "duration_hours": 120,
        "duration_weeks": "16 недель",
        "price": "50000",
    }


# ============================================================
# Пользователи
# ============================================================
@pytest.fixture
def university_admin_user(organization):
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
    return User.objects.create_user(
        username="regular_user",
        email="user@example.com",
        password="testpass123",
        user_type="regular",
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        user_type="admin",
    )


@pytest.fixture
def authenticated_university_user(university_admin_user, organization):
    user = university_admin_user
    user.organization = organization
    user.save()
    return user


@pytest.fixture
def test_employer_user(organization):
    return User.objects.create_user(
        username="test_employer",
        email="employer@test.com",
        password="testpass123",
        user_type="employer",
        organization=organization,
        last_name="Иванов",
        first_name="Иван",
    )


@pytest.fixture
def employer_user(organization):
    return User.objects.create_user(
        username="employer_user",
        email="employer_user@test.com",
        password="testpass123",
        user_type="employer",
        organization=organization,
        last_name="Петров",
        first_name="Петр",
    )


# ============================================================
# Работники (с профилем)
# ============================================================
@pytest.fixture
def test_employee_user(organization):
    """Работник с организацией и профилем."""
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
    EmployeeProfile.objects.create(
        user=user,
        snils="123-456-789 01",
        organization=organization,
        position="Начальник цеха",
        position_level="middle",
    )
    return user


@pytest.fixture
def test_employee_user2(organization):
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


@pytest.fixture
def user_with_employee_profile(test_employee_user):
    """Алиас для обратной совместимости — тот же работник с профилем."""
    return test_employee_user


@pytest.fixture
def unemployed_user():
    """Безработный работник с профилем, без организации."""
    user = User.objects.create_user(
        username="unemployed",
        email="unemployed@test.com",
        password="unemployed123",
        user_type="employee",
        last_name="Сидоров",
        first_name="Семён",
        patronymic="Семёнович",
        snils="555-555-555 55",
    )
    EmployeeProfile.objects.create(
        user=user,
        snils="555-555-555 55",
        organization=None,
        is_unemployed=True,
        position="",
    )
    return user


@pytest.fixture
def svo_user(organization):
    """Участник СВО с профилем и организацией."""
    user = User.objects.create_user(
        username="svo_user",
        email="svo@test.com",
        password="svo123",
        user_type="employee",
        organization=organization,
        last_name="Смирнов",
        first_name="Сергей",
        snils="777-777-777 77",
    )
    EmployeeProfile.objects.create(
        user=user,
        snils="777-777-777 77",
        organization=organization,
        is_svo_participant=True,
        position="Специалист",
    )
    return user


# ============================================================
# Опросы
# ============================================================
@pytest.fixture
def survey_category():
    return SurveyCategory.objects.create(
        name="RIASEC",
        description="Опросник профессиональных склонностей",
        is_active=True,
    )


@pytest.fixture
def survey_session(regular_user, survey_category):
    from apps.surveys.models import SurveySession as Session

    return Session.objects.create(
        user=regular_user,
        category=survey_category,
        status="completed",
        completed_at=timezone.now(),
    )


# ============================================================
# Рекомендации курсов
# ============================================================
@pytest.fixture
def course_recommendation(regular_user, course):
    return CourseRecommendation.objects.create(
        user=regular_user,
        course=course,
        reason="Тестовая рекомендация",
        relevance_score=0.85,
        order=1,
    )


@pytest.fixture
def course_recommendations(regular_user, multiple_courses):
    recommendations = []
    for i, c in enumerate(multiple_courses[:5]):
        rec = CourseRecommendation.objects.create(
            user=regular_user,
            course=c,
            reason=f"Рекомендация {i+1}",
            relevance_score=0.9 - (i * 0.1),
            order=i,
        )
        recommendations.append(rec)
    return recommendations


@pytest.fixture
def recommendation_task(regular_user):
    return RecommendationTask.objects.create(
        user=regular_user,
        task_id="test-task-123",
        status="pending",
    )


# ============================================================
# Выбранные курсы
# ============================================================
@pytest.fixture
def selected_course(test_employee_user, course):
    """Выбранный курс работником с профилем и организацией."""
    return SelectedCourse.objects.create(
        user=test_employee_user,
        course=course,
    )


@pytest.fixture
def selected_course_unemployed(unemployed_user, course):
    """Выбранный курс безработным."""
    return SelectedCourse.objects.create(
        user=unemployed_user,
        course=course,
    )


@pytest.fixture
def selected_course_svo(svo_user, course):
    """Выбранный курс участником СВО."""
    return SelectedCourse.objects.create(
        user=svo_user,
        course=course,
    )


@pytest.fixture
def approved_course(selected_course, admin_user):
    """Одобренный выбранный курс."""
    return ApprovedSelectedCourse.objects.create(
        selected_course=selected_course,
        status="approved",
        approved_by=admin_user,
        approved_at=timezone.now(),
    )


@pytest.fixture
def approved_course_unemployed(selected_course_unemployed, admin_user):
    """Одобренный выбранный курс безработным."""
    return ApprovedSelectedCourse.objects.create(
        selected_course=selected_course_unemployed,
        status="approved",
        approved_by=admin_user,
        approved_at=timezone.now(),
    )


# ============================================================
# Рекомендации от работодателя
# ============================================================
@pytest.fixture
def employer_recommendation(test_employer_user, test_employee_user, course):
    return EmployerRecommendation.objects.create(
        employer=test_employer_user,
        employee=test_employee_user,
        course=course,
        reason="Тестовая рекомендация",
    )


# ============================================================
# Просмотрщик
# ============================================================
@pytest.fixture
def viewer_user():
    """Пользователь-просмотрщик (is_staff, в группе «Просмотрщик»)."""
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
        for action in ("view", "change", "add", "delete"):
            codename = f"{action}_{model._meta.model_name}"
            perm, _ = Permission.objects.get_or_create(
                content_type=ct,
                codename=codename,
                defaults={"name": f"Can {action} {model._meta.model_name}"},
            )
            group.permissions.add(perm)

    return user


@pytest.fixture
def viewer_client(client, viewer_user):
    client.force_login(viewer_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


# ============================================================
# Request factory и messages
# ============================================================
@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def mock_request_with_messages(request_factory):
    req = request_factory.get("/")
    req.user = None
    setattr(req, "session", "session")
    messages = FallbackStorage(req)
    setattr(req, "_messages", messages)
    return req


# ============================================================
# Goal setting
# ============================================================
@pytest.fixture
def test_question_choice():
    from apps.goal_setting.models import Question, QuestionOption

    question = Question.objects.create(
        text="Какой ваш любимый язык программирования?",
        question_type="choice",
        is_active=True,
        order=1,
    )
    QuestionOption.objects.create(
        question=question, value="python", label="Python", order=1
    )
    QuestionOption.objects.create(
        question=question, value="javascript", label="JavaScript", order=2
    )
    return question


@pytest.fixture
def test_question_text():
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
    from apps.goal_setting.models import Question, QuestionOption

    question = Question.objects.create(
        text="Какие технологии вы используете?",
        question_type="multiple_choice",
        is_active=True,
        order=3,
        is_multiple=True,
    )
    QuestionOption.objects.create(
        question=question, value="docker", label="Docker", order=1
    )
    QuestionOption.objects.create(
        question=question, value="kubernetes", label="Kubernetes", order=2
    )
    return question


@pytest.fixture
def test_question_date_range():
    from apps.goal_setting.models import Question

    return Question.objects.create(
        text="Укажите период вашей работы на последнем месте",
        question_type="date_range",
        is_active=True,
        order=4,
    )


@pytest.fixture
def test_question_inactive():
    from apps.goal_setting.models import Question

    return Question.objects.create(
        text="Неактивный вопрос",
        question_type="text",
        is_active=False,
        order=999,
    )


# ============================================================
# Request с messages для тестов actions
# ============================================================
@pytest.fixture
def admin_request(rf, admin_user):
    """GET-запрос с пользователем-админом и рабочим messages-хранилищем."""
    request = rf.get("/")
    request.user = admin_user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request
