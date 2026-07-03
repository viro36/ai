import pytest
from django.contrib.auth import get_user_model
from apps.goal_setting.models import Question, QuestionOption, GoalSettingResponse

User = get_user_model()


@pytest.fixture
def test_user():
    """Фикстура для тестового пользователя"""
    return User.objects.create_user(
        username="test_user",
        email="test@example.com",
        password="testpass123",
        user_type="employee",
        last_name="Тестов",
        first_name="Пользователь",
    )


@pytest.fixture
def test_user2():
    """Фикстура для второго тестового пользователя"""
    return User.objects.create_user(
        username="test_user2",
        email="test2@example.com",
        password="testpass123",
        user_type="employee",
        last_name="Второй",
        first_name="Пользователь",
    )


@pytest.fixture
def test_question_choice():
    """Фикстура для вопроса с выбором"""
    return Question.objects.create(
        text="Какой ваш любимый язык программирования?",
        question_type="choice",
        description="Выберите один вариант",
        is_required=True,
        order=1,
        is_active=True,
        has_custom_option=True,
        custom_option_label="Другой язык",
    )


@pytest.fixture
def test_question_text():
    """Фикстура для текстового вопроса"""
    return Question.objects.create(
        text="Опишите ваш опыт работы",
        question_type="text",
        description="Расскажите подробно",
        is_required=True,
        order=2,
        is_active=True,
        max_length=1000,
    )


@pytest.fixture
def test_question_multiple_choice():
    """Фикстура для вопроса с множественным выбором"""
    return Question.objects.create(
        text="Какие технологии вы используете?",
        question_type="multiple_choice",
        description="Выберите все подходящие варианты",
        is_required=True,
        order=3,
        is_active=True,
        is_multiple=True,
    )


@pytest.fixture
def test_question_multiple_choice_options(test_question_multiple_choice):
    """Фикстура для вариантов ответов на вопрос с множественным выбором"""
    options = []
    labels = ["Python", "JavaScript", "Java", "C++", "Ruby", "Rails"]
    for i, label in enumerate(labels):
        opt = QuestionOption.objects.create(
            question=test_question_multiple_choice,
            value=label.lower(),
            label=label,
            is_custom=False,
            order=i,
        )
        options.append(opt)
    return options


@pytest.fixture
def test_question_date_range():
    """Фикстура для вопроса с диапазоном дат"""
    return Question.objects.create(
        text="Укажите желаемый период обучения",
        question_type="date_range",
        description="Выберите даты",
        is_required=True,
        order=4,
        is_active=True,
    )


@pytest.fixture
def test_question_options(test_question_choice):
    """Фикстура для вариантов ответов"""
    options = []
    labels = ["Python", "JavaScript", "Java", "C++"]
    for i, label in enumerate(labels):
        opt = QuestionOption.objects.create(
            question=test_question_choice,
            value=label.lower(),
            label=label,
            is_custom=False,
            order=i,
        )
        options.append(opt)
    return options


@pytest.fixture
def test_goal_setting_response(test_user, test_question_choice, test_question_options):
    """Фикстура для ответа пользователя на вопрос"""
    return GoalSettingResponse.objects.create(
        user=test_user,
        question=test_question_choice,
        answer_option=test_question_options[0],  # Python
    )


@pytest.fixture
def auth_client(client, test_user):
    """Фикстура для авторизованного клиента"""
    client.force_login(test_user)
    return client


@pytest.fixture
def admin_user():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client
