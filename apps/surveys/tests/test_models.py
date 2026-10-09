import pytest
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.accounts.models import EmployeeProfile
from apps.organizations.models import Organization
from apps.surveys.models import (
    DiagnosticKitResult,
    SurveyBlock,
    SurveyQuestion,
    SurveyQuestionOption,
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

    def test_unique_together_same_group(self, user, survey_question, survey_session):
        """В рамках одной группы дубли не допускаются"""
        UserSurveyResponse.objects.create(
            user=user,
            question=survey_question,
            session=survey_session,
            group="А",
            score=4,
        )
        with pytest.raises(IntegrityError):
            UserSurveyResponse.objects.create(
                user=user,
                question=survey_question,
                session=survey_session,
                group="А",
                score=5,
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


# ============================================================
# SurveyQuestionOption
# ============================================================


@pytest.mark.django_db
class TestSurveyQuestionOption:
    """Тесты для модели SurveyQuestionOption"""

    def test_create_option(self, diagnostic_question):
        option = SurveyQuestionOption.objects.create(
            question=diagnostic_question,
            group="А",
            text="А1) Что-то",
            is_correct=False,
            order=1,
        )
        assert option.id is not None
        assert option.group == "А"
        assert option.is_correct is False

    def test_str_with_group(self, diagnostic_question):
        option = SurveyQuestionOption.objects.create(
            question=diagnostic_question,
            group="Б",
            text="Б2) Текст",
            is_correct=True,
            order=2,
        )
        assert "[Б]" in str(option)
        assert "Б2" in str(option)

    def test_str_without_group(self, diagnostic_question):
        option = SurveyQuestionOption.objects.create(
            question=diagnostic_question,
            group=None,
            text="Без группы",
            order=1,
        )
        assert "[None]" not in str(option)
        assert "Без группы" in str(option)

    def test_ordering(self, diagnostic_question):
        o3 = SurveyQuestionOption.objects.create(
            question=diagnostic_question, group="А", text="3", order=3
        )
        o1 = SurveyQuestionOption.objects.create(
            question=diagnostic_question, group="А", text="1", order=1
        )
        o2 = SurveyQuestionOption.objects.create(
            question=diagnostic_question, group="А", text="2", order=2
        )
        opts = list(SurveyQuestionOption.objects.filter(question=diagnostic_question))
        assert opts[0].order == 1
        assert opts[1].order == 2
        assert opts[2].order == 3

    def test_cascade_delete(self, diagnostic_question):
        SurveyQuestionOption.objects.create(
            question=diagnostic_question, group="А", text="Удалится", order=1
        )
        diagnostic_question.delete()
        assert SurveyQuestionOption.objects.count() == 0


# ============================================================
# UserSurveyResponse.group
# ============================================================


@pytest.mark.django_db
class TestUserSurveyResponseGroup:
    """Тесты поля group в UserSurveyResponse"""

    def test_score_optional(self, user, survey_question, survey_session):
        """score может быть NULL для опросов с опциями"""
        r = UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=survey_question,
            group="А",
            score=None,
        )
        assert r.score is None
        assert r.group == "А"

    def test_selected_option_optional(self, user, survey_question, survey_session):
        """selected_option может быть NULL для опросов со шкалой"""
        r = UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=survey_question,
            score=3,
        )
        assert r.selected_option is None
        assert r.group is None

    def test_unique_together_with_group(
        self, user, diagnostic_question, diagnostic_options, survey_session
    ):
        """4 ответа на один вопрос — по одному на группу — допустимы"""
        for letter in ("А", "Б", "В", "Г"):
            UserSurveyResponse.objects.create(
                user=user,
                session=survey_session,
                question=diagnostic_question,
                group=letter,
                selected_option=diagnostic_options[0],
                score=1,
            )
        assert (
            UserSurveyResponse.objects.filter(
                user=user, question=diagnostic_question, session=survey_session
            ).count()
            == 4
        )

    def test_unique_together_same_group_fails(
        self, user, diagnostic_question, diagnostic_options, survey_session
    ):
        """Два ответа с одинаковой группой на один вопрос — ошибка"""
        UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=diagnostic_question,
            group="А",
            selected_option=diagnostic_options[0],
            score=1,
        )
        with pytest.raises(IntegrityError):
            UserSurveyResponse.objects.create(
                user=user,
                session=survey_session,
                question=diagnostic_question,
                group="А",
                selected_option=diagnostic_options[1],
                score=1,
            )

    def test_str_with_group(self, user, diagnostic_question, survey_session):
        r = UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=diagnostic_question,
            group="Б",
            score=1,
        )
        assert "Б" in str(r)

    def test_str_without_group(self, user, survey_question, survey_session):
        r = UserSurveyResponse.objects.create(
            user=user,
            session=survey_session,
            question=survey_question,
            score=3,
        )
        assert "3" in str(r)


# ============================================================
# SurveyCategory.is_available_for
# ============================================================


@pytest.mark.django_db
class TestSurveyCategoryAvailability:
    """Тесты метода is_available_for"""

    def test_available_for_employee_in_matching_org(
        self, diagnostic_category, general_education_type, director_position
    ):
        """Работник в организации «Общее образование» с нужной должностью"""
        User = get_user_model()
        org = Organization.objects.create(
            inn="123456789012",
            full_name="Школа №1",
            short_name="Школа №1",
            address_raw="г. Воронеж",
            organization_type=general_education_type,
        )
        user = User.objects.create_user(
            username="emp",
            password="x",
            user_type="employee",
            organization=org,
        )
        EmployeeProfile.objects.create(
            user=user,
            snils="123-456-789 01",
            organization=org,
            position="Директор школы",
            position_level="top",
        )
        diagnostic_category.target_positions.add(director_position)

        assert diagnostic_category.is_available_for(user) is True

    def test_not_available_for_wrong_org_type(self, diagnostic_category, it_type):
        """Работник в организации другого типа — опрос недоступен"""
        from apps.accounts.models import EmployeeProfile
        from apps.organizations.models import Organization
        from django.contrib.auth import get_user_model

        User = get_user_model()
        org = Organization.objects.create(
            inn="999999999999",
            full_name="ООО Айти",
            short_name="ООО Айти",
            address_raw="г. Воронеж",
            organization_type=it_type,
        )
        user = User.objects.create_user(
            username="emp2",
            password="x",
            user_type="employee",
            organization=org,
        )
        EmployeeProfile.objects.create(
            user=user,
            snils="987-654-321 01",
            organization=org,
            position="Разработчик",
            position_level="specialist",
        )
        assert diagnostic_category.is_available_for(user) is False

    def test_not_available_for_wrong_user_type(
        self, diagnostic_category, general_education_type
    ):
        """Работодатель не видит опрос для работников"""
        User = get_user_model()
        user = User.objects.create_user(
            username="emp3",
            password="x",
            user_type="employer",
        )
        assert diagnostic_category.is_available_for(user) is False

    def test_available_when_no_restrictions(self, survey_category, user):
        """Без ограничений — доступен всем"""
        assert survey_category.is_available_for(user) is True

    def test_not_available_wrong_position(
        self,
        diagnostic_category,
        general_education_type,
        director_position,
        teacher_position,
    ):
        """У работника другая должность — недоступен"""
        User = get_user_model()
        org = Organization.objects.create(
            inn="555555555555",
            full_name="Школа №2",
            short_name="Школа №2",
            address_raw="г. Воронеж",
            organization_type=general_education_type,
        )
        user = User.objects.create_user(
            username="emp4",
            password="x",
            user_type="employee",
            organization=org,
        )
        EmployeeProfile.objects.create(
            user=user,
            snils="111-222-333 44",
            organization=org,
            position="Учитель",
            position_level="specialist",
        )
        diagnostic_category.target_positions.add(director_position)

        assert diagnostic_category.is_available_for(user) is False


# ============================================================
# DiagnosticKitResult
# ============================================================


@pytest.mark.django_db
class TestDiagnosticKitResult:
    """Тесты модели DiagnosticKitResult"""

    def test_create_result(self, completed_session):
        r = DiagnosticKitResult.objects.create(
            session=completed_session,
            work1_score=8,
            work2_score=6,
            work3_score=6,
            work4_score=8,
            total_score=28,
        )
        assert r.id is not None
        assert r.total_score == 28

    def test_str_method(self, completed_session):
        r = DiagnosticKitResult.objects.create(
            session=completed_session,
            work1_score=10,
            work2_score=10,
            work3_score=10,
            work4_score=10,
            total_score=40,
        )
        assert "40/40" in str(r)

    # ---------- Шкала по работе ----------

    @pytest.mark.parametrize(
        "score,expected_code",
        [
            (0, "low"),
            (4, "low"),
            (5, "medium"),
            (6, "medium"),
            (7, "high"),
            (8, "high"),
            (9, "expert"),
            (10, "expert"),
        ],
    )
    def test_level_for_work(self, score, expected_code):
        assert DiagnosticKitResult.level_for_work(score)["code"] == expected_code

    # ---------- Интегральная шкала ----------

    @pytest.mark.parametrize(
        "score,expected_code",
        [
            (0, "low"),
            (16, "low"),
            (17, "medium"),
            (26, "medium"),
            (27, "high"),
            (34, "high"),
            (35, "expert"),
            (40, "expert"),
        ],
    )
    def test_level_for_total(self, score, expected_code):
        assert DiagnosticKitResult.level_for_total(score)["code"] == expected_code

    # ---------- get_works_data ----------

    def test_get_works_data_uses_block_subtitle(
        self, completed_session, diagnostic_block
    ):
        """Название работы берётся из subtitle блока"""
        completed_session.category = diagnostic_block.category
        completed_session.save()

        r = DiagnosticKitResult.objects.create(
            session=completed_session,
            work1_score=8,
            work2_score=6,
            work3_score=6,
            work4_score=8,
            total_score=28,
        )
        works = r.get_works_data()
        assert len(works) == 4
        assert (
            works[0]["name"] == "Управление образовательной деятельностью и качеством"
        )
        assert works[0]["score"] == 8
        assert works[0]["percent"] == 80
        assert works[0]["level"]["code"] == "high"

    def test_get_works_data_fallback_to_title(
        self, completed_session, diagnostic_category
    ):
        """Если subtitle пуст — берётся title блока"""
        completed_session.category = diagnostic_category
        completed_session.save()

        SurveyBlock.objects.create(
            category=diagnostic_category,
            title="Диагностическая работа 1",
            subtitle=None,
            order=1,
        )

        r = DiagnosticKitResult.objects.create(
            session=completed_session,
            work1_score=5,
            work2_score=5,
            work3_score=5,
            work4_score=5,
            total_score=20,
        )
        works = r.get_works_data()
        assert works[0]["name"] == "Диагностическая работа 1"
