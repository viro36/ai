import pytest
from django.db import IntegrityError

from apps.surveys.models import (
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

# ============================================================
# Тесты для SurveyCategory
# ============================================================


@pytest.mark.django_db
class TestSurveyCategory:
    """Тесты для модели SurveyCategory"""

    def test_create_category(self, survey_category):
        assert survey_category.id is not None
        assert survey_category.name == "Тестовый опрос"
        assert survey_category.is_active is True

    def test_str_method(self, survey_category):
        assert str(survey_category) == "Тестовый опрос"

    def test_get_questions_count(self, survey_category, survey_block, survey_question):
        SurveyQuestion.objects.create(
            block=survey_block, text="Второй вопрос", q_number=2
        )
        assert survey_category.get_questions_count() == 2

    def test_get_questions_count_empty(self, survey_category):
        assert survey_category.get_questions_count() == 0

    def test_get_display_description_with_import(self, survey_category):
        survey_category.description = "Импортирован из Excel: test.xlsx"
        assert (
            survey_category.get_display_description()
            == "Пройдите опрос, чтобы оценить свои навыки"
        )

    def test_get_display_description_normal(self, survey_category):
        survey_category.description = "Обычное описание"
        assert survey_category.get_display_description() == "Обычное описание"

    def test_get_display_description_empty(self, survey_category):
        survey_category.description = None
        assert (
            survey_category.get_display_description()
            == "Пройдите опрос, чтобы оценить свои навыки"
        )


# ============================================================
# Тесты для SurveyBlock
# ============================================================


@pytest.mark.django_db
class TestSurveyBlock:
    """Тесты для модели SurveyBlock"""

    def test_create_block(self, survey_category, survey_block):
        assert survey_block.id is not None
        assert survey_block.category == survey_category
        assert survey_block.title == "Тестовый блок"

    def test_str_method(self, survey_category, survey_block):
        expected = f"{survey_category.name} - {survey_block.title}"
        assert str(survey_block) == expected

    def test_block_order(self, survey_category):
        block1 = SurveyBlock.objects.create(
            category=survey_category, title="Блок 1", order=1
        )
        block2 = SurveyBlock.objects.create(
            category=survey_category, title="Блок 2", order=2
        )
        block3 = SurveyBlock.objects.create(
            category=survey_category, title="Блок 3", order=0
        )

        blocks = list(
            SurveyBlock.objects.filter(category=survey_category).order_by("order")
        )
        assert blocks[0].order == 0
        assert blocks[0].title == "Блок 3"


# ============================================================
# Тесты для ScaleLabel
# ============================================================


@pytest.mark.django_db
class TestScaleLabel:
    """Тесты для модели ScaleLabel"""

    def test_create_global_scale_label(self):
        label = ScaleLabel.objects.create(category=None, scale_value=1, label="Тест")
        assert label.id is not None
        assert label.category is None

    def test_create_category_scale_label(self, survey_category):
        label = ScaleLabel.objects.create(
            category=survey_category, scale_value=1, label="Своя"
        )
        assert label.category == survey_category

    def test_unique_together(self, survey_category):
        ScaleLabel.objects.create(
            category=survey_category, scale_value=1, label="Первый"
        )
        with pytest.raises(IntegrityError):
            ScaleLabel.objects.create(
                category=survey_category, scale_value=1, label="Дубликат"
            )

    def test_str_method_global(self):
        label = ScaleLabel.objects.create(category=None, scale_value=1, label="Тест")
        assert str(label) == "Глобальная - 1 — Тест"

    def test_str_method_with_category(self, survey_category):
        label = ScaleLabel.objects.create(
            category=survey_category, scale_value=1, label="Тест"
        )
        assert str(label) == f"{survey_category.name} - 1 — Тест"


# ============================================================
# Тесты для SurveyQuestion
# ============================================================


@pytest.mark.django_db
class TestSurveyQuestion:
    """Тесты для модели SurveyQuestion"""

    def test_create_question(self, survey_block):
        question = SurveyQuestion.objects.create(
            block=survey_block, text="Вопрос?", q_number=1
        )
        assert question.id is not None
        assert question.text == "Вопрос?"

    def test_str_method(self, survey_block):
        question = SurveyQuestion.objects.create(
            block=survey_block, text="Короткий вопрос", q_number=1
        )
        expected = f"{survey_block.title}: Короткий вопрос"
        assert str(question) == expected

    def test_default_is_active(self, survey_block):
        question = SurveyQuestion.objects.create(
            block=survey_block, text="Вопрос", q_number=1
        )
        assert question.is_active is True

    def test_ordering(self, survey_block):
        q1 = SurveyQuestion.objects.create(
            block=survey_block, text="Первый", q_number=1
        )
        q3 = SurveyQuestion.objects.create(
            block=survey_block, text="Третий", q_number=3
        )
        q2 = SurveyQuestion.objects.create(
            block=survey_block, text="Второй", q_number=2
        )

        questions = list(
            SurveyQuestion.objects.filter(block=survey_block).order_by("q_number")
        )
        assert questions[0].q_number == 1
        assert questions[1].q_number == 2
        assert questions[2].q_number == 3


# ============================================================
# Тесты для SurveySession
# ============================================================


@pytest.mark.django_db
class TestSurveySession:
    """Тесты для модели SurveySession"""

    def test_create_session(self, user, survey_category, survey_block, survey_question):
        session = SurveySession.objects.create(
            user=user,
            category=survey_category,
            attempt=1,
            status="in_progress",
            current_block=survey_block,
            current_question=survey_question,
        )
        assert session.id is not None
        assert session.attempt == 1

    def test_str_method(self, user, survey_category):
        session = SurveySession.objects.create(
            user=user, category=survey_category, attempt=2, status="completed"
        )
        expected = f"{user} - {survey_category.name} (попытка 2) - Завершён"
        assert str(session) == expected

    def test_unique_together(self, user, survey_category):
        SurveySession.objects.create(user=user, category=survey_category, attempt=1)
        with pytest.raises(IntegrityError):
            SurveySession.objects.create(user=user, category=survey_category, attempt=1)

    def test_progress_empty(self, user, survey_category):
        session = SurveySession.objects.create(
            user=user, category=survey_category, attempt=1
        )
        assert session.progress == 0

    def test_progress_with_questions(
        self, user, survey_category, survey_block, survey_question, survey_session
    ):
        # Ответ без привязки к сессии
        UserSurveyResponse.objects.create(user=user, question=survey_question, score=5)
        assert survey_session.progress == 0

        # Ответ с привязкой к сессии
        UserSurveyResponse.objects.create(
            user=user, session=survey_session, question=survey_question, score=5
        )
        assert survey_session.progress == 100


# ============================================================
# Тесты для UserSurveyResponse
# ============================================================


@pytest.mark.django_db
class TestUserSurveyResponse:
    """Тесты для модели UserSurveyResponse"""

    def test_create_response(self, user, survey_question):
        response = UserSurveyResponse.objects.create(
            user=user, question=survey_question, score=4
        )
        assert response.id is not None
        assert response.score == 4

    def test_unique_together(self, user, survey_question, survey_session):
        UserSurveyResponse.objects.create(
            user=user, question=survey_question, session=survey_session, score=4
        )
        with pytest.raises(IntegrityError):
            UserSurveyResponse.objects.create(
                user=user, question=survey_question, session=survey_session, score=5
            )

    def test_str_method(self, user, survey_question):
        response = UserSurveyResponse.objects.create(
            user=user, question=survey_question, score=3
        )
        expected = f"{user} - {survey_question.text[:30]} - 3"
        assert str(response) == expected


# ============================================================
# Тесты для SurveyInterpretation
# ============================================================


@pytest.mark.django_db
class TestSurveyInterpretation:
    """Тесты для модели SurveyInterpretation"""

    def test_create_interpretation(self):
        interpretation = SurveyInterpretation.objects.create(
            survey_type="digcomp",
            code="A2",
            user_type="employee",
            title="Базовый уровень",
            is_active=True,
        )
        assert interpretation.id is not None

    def test_str_method(self):
        interpretation = SurveyInterpretation.objects.create(
            survey_type="riasec",
            code="RIA",
            user_type="common",
            title="Технический специалист",
        )
        assert str(interpretation) == "RIASEC - RIA - Общий"

    def test_unique_together(self):
        SurveyInterpretation.objects.create(
            survey_type="big5", code="high", user_type="employee", title="Высокий"
        )
        with pytest.raises(IntegrityError):
            SurveyInterpretation.objects.create(
                survey_type="big5", code="high", user_type="employee", title="Дубликат"
            )

    def test_ordering(self):
        i1 = SurveyInterpretation.objects.create(
            survey_type="digcomp", code="C1", user_type="common", title="C1", order=100
        )
        i2 = SurveyInterpretation.objects.create(
            survey_type="digcomp", code="A1", user_type="common", title="A1", order=10
        )
        i3 = SurveyInterpretation.objects.create(
            survey_type="digcomp", code="B1", user_type="common", title="B1", order=50
        )

        interpretations = list(
            SurveyInterpretation.objects.filter(survey_type="digcomp")
        )
        assert interpretations[0].order == 10
        assert interpretations[1].order == 50
        assert interpretations[2].order == 100


# ============================================================
# Тесты для DigCompResult
# ============================================================


@pytest.mark.django_db
class TestDigCompResult:
    """Тесты для модели DigCompResult"""

    def test_create_result(self, completed_session):
        result = DigCompResult.objects.create(
            session=completed_session,
            area1_score=42,
            area2_score=35,
            area3_score=28,
            area4_score=40,
            area5_score=38,
        )
        assert result.id is not None
        assert result.area1_score == 42

    def test_one_to_one_relation(self, completed_session):
        DigCompResult.objects.create(
            session=completed_session,
            area1_score=40,
            area2_score=40,
            area3_score=40,
            area4_score=40,
            area5_score=40,
        )
        with pytest.raises(IntegrityError):
            DigCompResult.objects.create(
                session=completed_session,
                area1_score=30,
                area2_score=30,
                area3_score=30,
                area4_score=30,
                area5_score=30,
            )

    def test_str_method(self, completed_session):
        result = DigCompResult.objects.create(
            session=completed_session,
            area1_score=50,
            area2_score=50,
            area3_score=50,
            area4_score=50,
            area5_score=50,
        )
        assert str(result) == f"{completed_session.user}"


# ============================================================
# Тесты для RiasacResult
# ============================================================


@pytest.mark.django_db
class TestRiasacResult:
    """Тесты для модели RiasacResult"""

    def test_create_result(self, completed_session):
        result = RiasacResult.objects.create(
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
        assert result.id is not None
        assert result.career_code == "RSE"

    def test_get_scores_dict(self, completed_session):
        result = RiasacResult.objects.create(
            session=completed_session,
            r_score=40,
            i_score=35,
            a_score=25,
            s_score=45,
            e_score=30,
            c_score=20,
            career_code="RSE",
            dominant_types="",
        )
        scores = result.get_scores_dict()
        assert scores["R"] == 40
        assert scores["S"] == 45

    def test_get_level_for_score(self, completed_session):
        result = RiasacResult.objects.create(
            session=completed_session,
            r_score=40,
            i_score=35,
            a_score=25,
            s_score=45,
            e_score=30,
            c_score=20,
            career_code="RSE",
            dominant_types="",
        )
        assert result.get_level_for_score(15) == "low"
        assert result.get_level_for_score(25) == "medium"
        assert result.get_level_for_score(40) == "high"

    def test_str_method(self, completed_session):
        result = RiasacResult.objects.create(
            session=completed_session,
            r_score=40,
            i_score=35,
            a_score=25,
            s_score=45,
            e_score=30,
            c_score=20,
            career_code="RSE",
            dominant_types="",
        )
        assert str(result) == f"{completed_session.user} - RSE"


# ============================================================
# Тесты для Big5Result
# ============================================================


@pytest.mark.django_db
class TestBig5Result:
    """Тесты для модели Big5Result"""

    def test_create_result(self, completed_session):
        result = Big5Result.objects.create(
            session=completed_session,
            extraversion_score=35,
            agreeableness_score=42,
            conscientiousness_score=38,
            neuroticism_score=25,
            openness_score=40,
        )
        assert result.id is not None

    def test_str_method(self, completed_session):
        result = Big5Result.objects.create(
            session=completed_session,
            extraversion_score=35,
            agreeableness_score=42,
            conscientiousness_score=38,
            neuroticism_score=25,
            openness_score=40,
        )
        assert str(result) == f"{completed_session.user} - Big5"


# ============================================================
# Тесты для GardnerResult
# ============================================================


@pytest.mark.django_db
class TestGardnerResult:
    """Тесты для модели GardnerResult"""

    def test_create_result(self, completed_session):
        result = GardnerResult.objects.create(
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
        assert result.id is not None

    def test_str_method(self, completed_session):
        result = GardnerResult.objects.create(
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
        assert str(result) == f"{completed_session.user} - Gardner"


# ============================================================
# Интеграционные тесты
# ============================================================


@pytest.mark.django_db
class TestIntegration:
    """Интеграционные тесты моделей"""

    def test_full_survey_flow(
        self, user, survey_category, survey_block, survey_question, global_scale_labels
    ):
        session = SurveySession.objects.create(
            user=user,
            category=survey_category,
            attempt=1,
            status="in_progress",
            current_block=survey_block,
            current_question=survey_question,
        )

        response = UserSurveyResponse.objects.create(
            user=user, session=session, question=survey_question, score=5
        )

        session.status = "completed"
        session.completed_at = pytest.importorskip("django.utils.timezone").now()
        session.save()

        result = DigCompResult.objects.create(
            session=session,
            area1_score=45,
            area2_score=45,
            area3_score=45,
            area4_score=45,
            area5_score=45,
        )

        assert session.progress == 100
        assert response.score == 5
        assert result.area1_score == 45
        assert session.responses.count() == 1
        assert session.digcomp_result == result

    def test_multiple_attempts(self, user, survey_category):
        session1 = SurveySession.objects.create(
            user=user, category=survey_category, attempt=1, status="completed"
        )
        session2 = SurveySession.objects.create(
            user=user, category=survey_category, attempt=2, status="completed"
        )
        session3 = SurveySession.objects.create(
            user=user, category=survey_category, attempt=3, status="in_progress"
        )

        completed = SurveySession.objects.filter(
            user=user, category=survey_category, status="completed"
        )
        in_progress = SurveySession.objects.filter(
            user=user, category=survey_category, status="in_progress"
        )

        assert completed.count() == 2
        assert in_progress.count() == 1
