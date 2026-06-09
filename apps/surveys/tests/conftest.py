import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.surveys.models import (
    SurveyCategory,
    SurveyBlock,
    SurveyQuestion,
    SurveySession,
    UserSurveyResponse,
    ScaleLabel,
    SurveyInterpretation,
    DigCompResult,
    RiasacResult,
    Big5Result,
    GardnerResult,
)

User = get_user_model()


# ============================================================
# Пользователи
# ============================================================


@pytest.fixture
def user():
    """Создание тестового пользователя"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def employer_user():
    """Создание тестового пользователя-работодателя"""
    return User.objects.create_user(
        username="employer",
        email="employer@example.com",
        password="testpass123",
        user_type="employer",
    )


@pytest.fixture
def university_user():
    """Создание тестового пользователя-вуза"""
    return User.objects.create_user(
        username="university",
        email="university@example.com",
        password="testpass123",
        user_type="university",
    )


@pytest.fixture
def admin_user():
    """Создание тестового администратора"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


# ============================================================
# Опросы (категории)
# ============================================================


@pytest.fixture
def survey_category():
    """Создание тестовой категории опроса"""
    return SurveyCategory.objects.create(
        name="Тестовый опрос",
        description="Описание тестового опроса",
        is_active=True,
        instruction_text="Инструкция для тестового опроса",
        result_description="<p>Описание результатов</p>",
    )


@pytest.fixture
def digcomp_category():
    """Создание категории DigCompEdu"""
    return SurveyCategory.objects.create(
        name="DigCompEdu", description="Опросник цифровой грамотности", is_active=True
    )


@pytest.fixture
def riasec_category():
    """Создание категории RIASEC"""
    return SurveyCategory.objects.create(
        name="RIASEC (Холланд)",
        description="Опросник профессиональных склонностей",
        is_active=True,
    )


@pytest.fixture
def big5_category():
    """Создание категории Big5"""
    return SurveyCategory.objects.create(
        name="Большая пятёрка (Big5)",
        description="Опросник личностных черт",
        is_active=True,
    )


@pytest.fixture
def gardner_category():
    """Создание категории Gardner"""
    return SurveyCategory.objects.create(
        name="Множественный интеллект (Гарднер)",
        description="Опросник типов интеллекта",
        is_active=True,
    )


@pytest.fixture
def inactive_category():
    """Создание неактивной категории опроса"""
    return SurveyCategory.objects.create(
        name="Неактивный опрос", description="Этот опрос недоступен", is_active=False
    )


# ============================================================
# Блоки вопросов
# ============================================================


@pytest.fixture
def survey_block(survey_category):
    """Создание тестового блока"""
    return SurveyBlock.objects.create(
        category=survey_category, title="Тестовый блок", order=1, is_active=True
    )


@pytest.fixture
def digcomp_blocks(digcomp_category):
    """Создание блоков для DigCompEdu"""
    blocks = []
    for i in range(1, 6):
        block = SurveyBlock.objects.create(
            category=digcomp_category, title=f"Область {i}", order=i, is_active=True
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def riasec_blocks(riasec_category):
    """Создание блоков для RIASEC"""
    blocks = []
    titles = [
        "Реалистичный (R)",
        "Исследовательский (I)",
        "Артистический (A)",
        "Социальный (S)",
        "Предпринимательский (E)",
        "Конвенциональный (C)",
    ]
    for i, title in enumerate(titles, 1):
        block = SurveyBlock.objects.create(
            category=riasec_category, title=title, order=i, is_active=True
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def big5_blocks(big5_category):
    """Создание блоков для Big5"""
    blocks = []
    titles = [
        "Экстраверсия",
        "Доброжелательность",
        "Добросовестность",
        "Нейротизм",
        "Открытость опыту",
    ]
    for i, title in enumerate(titles, 1):
        block = SurveyBlock.objects.create(
            category=big5_category, title=title, order=i, is_active=True
        )
        blocks.append(block)
    return blocks


@pytest.fixture
def gardner_blocks(gardner_category):
    """Создание блоков для Gardner"""
    blocks = []
    titles = [
        "Лингвистический",
        "Логико-математический",
        "Пространственный",
        "Музыкальный",
        "Телесно-кинестетический",
        "Межличностный",
        "Внутриличностный",
        "Натуралистический",
    ]
    for i, title in enumerate(titles, 1):
        block = SurveyBlock.objects.create(
            category=gardner_category, title=title, order=i, is_active=True
        )
        blocks.append(block)
    return blocks


# ============================================================
# Вопросы
# ============================================================


@pytest.fixture
def survey_question(survey_block):
    """Создание тестового вопроса"""
    return SurveyQuestion.objects.create(
        block=survey_block, text="Тестовый вопрос?", q_number=1, is_active=True
    )


@pytest.fixture
def multiple_questions(survey_block):
    """Создание нескольких вопросов в блоке"""
    questions = []
    for i in range(1, 11):
        question = SurveyQuestion.objects.create(
            block=survey_block, text=f"Вопрос {i}", q_number=i, is_active=True
        )
        questions.append(question)
    return questions


# ============================================================
# Сессии
# ============================================================


@pytest.fixture
def survey_session(user, survey_category, survey_block, survey_question):
    """Создание сессии опроса (в процессе)"""
    return SurveySession.objects.create(
        user=user,
        category=survey_category,
        attempt=1,
        status="in_progress",
        current_block=survey_block,
        current_question=survey_question,
    )


@pytest.fixture
def completed_session(user, survey_category, survey_block, survey_question):
    """Создание завершённой сессии опроса"""
    return SurveySession.objects.create(
        user=user,
        category=survey_category,
        attempt=1,
        status="completed",
        current_block=survey_block,
        current_question=survey_question,
        completed_at=timezone.now(),
    )


@pytest.fixture
def multiple_sessions(user, survey_category):
    """Создание нескольких сессий (разные попытки)"""
    sessions = []
    for attempt in range(1, 4):
        session = SurveySession.objects.create(
            user=user,
            category=survey_category,
            attempt=attempt,
            status="completed",
            completed_at=timezone.now(),
        )
        sessions.append(session)
    return sessions


# ============================================================
# Шкала оценок
# ============================================================


@pytest.fixture
def global_scale_labels():
    """Создание глобальных формулировок шкалы"""
    labels = []
    scale_data = {
        1: "Совсем не соответствует",
        2: "Скорее не соответствует",
        3: "Частично соответствует",
        4: "В основном соответствует",
        5: "Полностью соответствует",
    }
    for value, label in scale_data.items():
        scale_label = ScaleLabel.objects.create(
            category=None, scale_value=value, label=label
        )
        labels.append(scale_label)
    return labels


@pytest.fixture
def custom_scale_labels(survey_category):
    """Создание пользовательских формулировок шкалы для опроса"""
    labels = []
    scale_data = {
        1: "Совсем не про меня",
        2: "Скорее не про меня",
        3: "Иногда так бывает",
        4: "В основном про меня",
        5: "Полностью про меня",
    }
    for value, label in scale_data.items():
        scale_label = ScaleLabel.objects.create(
            category=survey_category, scale_value=value, label=label
        )
        labels.append(scale_label)
    return labels


# ============================================================
# Ответы
# ============================================================


@pytest.fixture
def survey_response(user, survey_question, survey_session):
    """Создание ответа на вопрос"""
    return UserSurveyResponse.objects.create(
        user=user, session=survey_session, question=survey_question, score=4
    )


@pytest.fixture
def all_responses(user, survey_session, multiple_questions):
    """Создание ответов на все вопросы блока"""
    responses = []
    for i, question in enumerate(multiple_questions, 1):
        response = UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=question,
            score=i % 5 + 1,  # случайная оценка от 1 до 5
        )
        responses.append(response)
    return responses


# ============================================================
# Интерпретации
# ============================================================


@pytest.fixture
def digcomp_interpretations():
    """Создание интерпретаций для DigCompEdu"""
    interpretations = []
    levels_data = {
        "A2": {"title": "Базовый уровень", "color": "success"},
        "B1": {"title": "Средний уровень", "color": "info"},
        "B2": {"title": "Продвинутый уровень", "color": "warning"},
        "C1": {"title": "Экспертный уровень", "color": "danger"},
    }
    for code, data in levels_data.items():
        for user_type in ["employee", "employer", "university", "common"]:
            interp = SurveyInterpretation.objects.create(
                survey_type="digcomp",
                code=code,
                user_type=user_type,
                title=data["title"],
                color=data["color"],
                is_active=True,
            )
            interpretations.append(interp)
    return interpretations


@pytest.fixture
def riasec_codes():
    """Создание интерпретаций для карьерных кодов RIASEC"""
    interpretations = []
    codes_data = {
        "RIA": "Технический специалист",
        "SEC": "Организатор",
        "EIC": "Предприниматель",
        "AIS": "Творческий специалист",
        "CSE": "Структурированный специалист",
        "IRE": "Исследователь",
    }
    for code, title in codes_data.items():
        for user_type in ["employee", "employer", "university", "common"]:
            interp = SurveyInterpretation.objects.create(
                survey_type="riasec",
                code=code,
                user_type=user_type,
                title=title,
                fields_list="Подходящие сферы",
                is_active=True,
            )
            interpretations.append(interp)
    return interpretations


# ============================================================
# Результаты опросов
# ============================================================


@pytest.fixture
def digcomp_result(completed_session):
    """Создание результата DigCompEdu"""
    return DigCompResult.objects.create(
        session=completed_session,
        area1_score=42,
        area2_score=35,
        area3_score=28,
        area4_score=40,
        area5_score=38,
    )


@pytest.fixture
def riasec_result(completed_session):
    """Создание результата RIASEC"""
    return RiasacResult.objects.create(
        session=completed_session,
        r_score=40,
        i_score=35,
        a_score=25,
        s_score=45,
        e_score=30,
        c_score=20,
        career_code="RSE",
        dominant_types="R:40, S:45, E:30",
    )


@pytest.fixture
def big5_result(completed_session):
    """Создание результата Big5"""
    return Big5Result.objects.create(
        session=completed_session,
        extraversion_score=35,
        agreeableness_score=42,
        conscientiousness_score=38,
        neuroticism_score=25,
        openness_score=40,
    )


@pytest.fixture
def gardner_result(completed_session):
    """Создание результата Gardner"""
    return GardnerResult.objects.create(
        session=completed_session,
        linguistic_score=30,
        logical_score=45,
        spatial_score=35,
        musical_score=20,
        kinesthetic_score=40,
        interpersonal_score=48,
        intrapersonal_score=38,
        naturalistic_score=25,
    )
