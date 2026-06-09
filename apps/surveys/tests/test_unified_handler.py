import pytest
from django.contrib.auth import get_user_model

from apps.surveys.services.survey_handlers.unified_handler import UnifiedSurveyHandler
from apps.surveys.models import (
    SurveyCategory,
    SurveyQuestion,
    SurveySession,
    UserSurveyResponse,
    SurveyInterpretation,
    DigCompResult,
    RiasacResult,
    Big5Result,
)

User = get_user_model()


# ============================================================
# Фикстуры для handler с сессией
# ============================================================


@pytest.fixture
def user_with_session(user, survey_category):
    """Создание пользователя и сессии"""
    session = SurveySession.objects.create(
        user=user, category=survey_category, attempt=1
    )
    return user, session


# ============================================================
# Тесты для get_survey_config (не требуют session)
# ============================================================


@pytest.mark.django_db
class TestGetSurveyConfig:
    """Тесты определения конфигурации опроса"""

    def test_digcomp_config(self, digcomp_category, user):
        """Тест конфигурации DigCompEdu"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)
        config = handler.get_survey_config()
        assert config["type"] == "digcomp"
        assert config["blocks"] == 5
        assert config["questions_per_block"] == 10
        assert config["max_total_score"] == 250

    def test_riasec_config(self, riasec_category, user):
        """Тест конфигурации RIASEC"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )
        handler = UnifiedSurveyHandler(riasec_category, session)
        config = handler.get_survey_config()
        assert config["type"] == "riasec"
        assert config["blocks"] == 6
        assert config["questions_per_block"] == 10
        assert config["max_total_score"] == 300

    def test_big5_config(self, big5_category, user):
        """Тест конфигурации Big5"""
        session = SurveySession.objects.create(
            user=user, category=big5_category, attempt=1
        )
        handler = UnifiedSurveyHandler(big5_category, session)
        config = handler.get_survey_config()
        assert config["type"] == "big5"
        assert config["blocks"] == 5
        assert config["questions_per_block"] == 10

    def test_gardner_config(self, gardner_category, user):
        """Тест конфигурации Gardner"""
        session = SurveySession.objects.create(
            user=user, category=gardner_category, attempt=1
        )
        handler = UnifiedSurveyHandler(gardner_category, session)
        config = handler.get_survey_config()
        assert config["type"] == "gardner"
        assert config["blocks"] == 8
        assert config["questions_per_block"] == 10

    def test_custom_config(self, survey_category, user):
        """Тест конфигурации пользовательского опроса"""
        session = SurveySession.objects.create(
            user=user, category=survey_category, attempt=1
        )
        handler = UnifiedSurveyHandler(survey_category, session)
        config = handler.get_survey_config()
        assert config["type"] == "custom"
        assert config["result_model"] is None


# ============================================================
# Тесты для get_level_for_score
# ============================================================


@pytest.mark.django_db
class TestGetLevelForScore:
    """Тесты определения уровня по баллу"""

    def test_digcomp_levels(self, digcomp_category, user):
        """Тест уровней DigCompEdu"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)
        config = {
            "level_ranges": {
                "A2": (10, 20),
                "B1": (21, 35),
                "B2": (36, 45),
                "C1": (46, 50),
            }
        }
        assert handler.get_level_for_score(15, config) == "A2"
        assert handler.get_level_for_score(25, config) == "B1"
        assert handler.get_level_for_score(40, config) == "B2"
        assert handler.get_level_for_score(48, config) == "C1"

    def test_riasec_levels(self, riasec_category, user):
        """Тест уровней RIASEC"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )
        handler = UnifiedSurveyHandler(riasec_category, session)
        config = {
            "level_ranges": {
                "low": (10, 20),
                "medium": (21, 35),
                "high": (36, 50),
            }
        }
        assert handler.get_level_for_score(15, config) == "low"
        assert handler.get_level_for_score(25, config) == "medium"
        assert handler.get_level_for_score(40, config) == "high"


# ============================================================
# Тесты для get_code_for_block
# ============================================================


@pytest.mark.django_db
class TestGetCodeForBlock:
    """Тесты получения кода блока RIASEC"""

    def test_codes(self, riasec_category, user):
        """Тест кодов RIASEC"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )
        handler = UnifiedSurveyHandler(riasec_category, session)
        assert handler.get_code_for_block(1) == "R"
        assert handler.get_code_for_block(2) == "I"
        assert handler.get_code_for_block(3) == "A"
        assert handler.get_code_for_block(4) == "S"
        assert handler.get_code_for_block(5) == "E"
        assert handler.get_code_for_block(6) == "C"
        assert handler.get_code_for_block(7) == ""


# ============================================================
# Тесты для get_interpretation
# ============================================================


@pytest.mark.django_db
class TestGetInterpretation:
    """Тесты получения интерпретаций из БД"""

    def test_get_existing_interpretation(self, user, digcomp_interpretations):
        """Тест получения существующей интерпретации"""
        category = SurveyCategory.objects.create(name="DigCompEdu")
        session = SurveySession.objects.create(user=user, category=category, attempt=1)
        handler = UnifiedSurveyHandler(category, session)

        result = handler.get_interpretation("A2", "employee")
        assert result is not None
        assert "title" in result

    def test_get_fallback_interpretation(self, user):
        """Тест получения интерпретации с fallback на common"""
        category = SurveyCategory.objects.create(name="DigCompEdu")
        session = SurveySession.objects.create(user=user, category=category, attempt=1)
        handler = UnifiedSurveyHandler(category, session)

        SurveyInterpretation.objects.create(
            survey_type="digcomp",
            code="B1",
            user_type="common",
            title="Средний уровень",
            is_active=True,
        )

        result = handler.get_interpretation("B1", "employee")
        assert result is not None
        assert result["title"] == "Средний уровень"

    def test_get_nonexistent_interpretation(self, user):
        """Тест получения несуществующей интерпретации"""
        category = SurveyCategory.objects.create(name="DigCompEdu")
        session = SurveySession.objects.create(user=user, category=category, attempt=1)
        handler = UnifiedSurveyHandler(category, session)

        result = handler.get_interpretation("XYZ", "employee")
        assert result is None


# ============================================================
# Тесты для calculate_results
# ============================================================


@pytest.mark.django_db
class TestCalculateResults:
    """Тесты расчёта результатов"""

    def test_custom_survey_returns_none(
        self, user, survey_category, survey_block, survey_question
    ):
        """Тест: пользовательский опрос возвращает None"""
        session = SurveySession.objects.create(
            user=user, category=survey_category, attempt=1
        )
        handler = UnifiedSurveyHandler(survey_category, session)

        UserSurveyResponse.objects.create(
            user=user, session=session, question=survey_question, score=4
        )

        result = handler.calculate_results(
            UserSurveyResponse.objects.filter(session=session)
        )
        assert result is None

    def test_digcomp_calculate_results(self, user, digcomp_category, digcomp_blocks):
        """Тест расчёта результатов DigCompEdu"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )

        for block in digcomp_blocks:
            for i in range(1, 11):
                question = SurveyQuestion.objects.create(
                    block=block, text=f"Вопрос {i}", q_number=i, is_active=True
                )
                UserSurveyResponse.objects.create(
                    user=user, session=session, question=question, score=5
                )

        handler = UnifiedSurveyHandler(digcomp_category, session)
        responses = UserSurveyResponse.objects.filter(session=session)
        result = handler.calculate_results(responses)

        assert result is not None
        assert isinstance(result, DigCompResult)
        assert result.area1_score == 50
        assert result.area2_score == 50
        assert result.area3_score == 50
        assert result.area4_score == 50
        assert result.area5_score == 50

    def test_riasec_calculate_results(self, user, riasec_category, riasec_blocks):
        """Тест расчёта результатов RIASEC с карьерным кодом"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )

        # Создаём вопросы и ответы с разными баллами
        scores_by_block = {}
        for idx, block in enumerate(riasec_blocks, 1):
            score_sum = 0
            for i in range(1, 11):
                question = SurveyQuestion.objects.create(
                    block=block, text=f"Вопрос {i}", q_number=i, is_active=True
                )
                # Даём максимальные баллы для первых трёх блоков
                if idx <= 3:
                    score = 5
                else:
                    score = 1
                UserSurveyResponse.objects.create(
                    user=user, session=session, question=question, score=score
                )
                score_sum += score
            scores_by_block[block.title] = score_sum

        handler = UnifiedSurveyHandler(riasec_category, session)
        responses = UserSurveyResponse.objects.filter(session=session)
        result = handler.calculate_results(responses)

        assert result is not None
        assert isinstance(result, RiasacResult)
        # Первые три блока должны быть в карьерном коде
        assert len(result.career_code) == 3

    def test_big5_calculate_results(self, user, big5_category, big5_blocks):
        """Тест расчёта результатов Big5"""
        session = SurveySession.objects.create(
            user=user, category=big5_category, attempt=1
        )

        for block in big5_blocks:
            for i in range(1, 11):
                question = SurveyQuestion.objects.create(
                    block=block, text=f"Вопрос {i}", q_number=i, is_active=True
                )
                UserSurveyResponse.objects.create(
                    user=user, session=session, question=question, score=4
                )

        handler = UnifiedSurveyHandler(big5_category, session)
        responses = UserSurveyResponse.objects.filter(session=session)
        result = handler.calculate_results(responses)

        assert result is not None
        assert isinstance(result, Big5Result)
        assert result.extraversion_score == 40
        assert result.agreeableness_score == 40


# ============================================================
# Тесты для get_results_context
# ============================================================


@pytest.mark.django_db
class TestGetResultsContext:
    """Тесты формирования контекста для отображения"""

    def test_digcomp_context(self, user, digcomp_category, digcomp_result):
        """Тест контекста для DigCompEdu"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)

        context = handler.get_results_context(digcomp_result)
        assert context["is_unified"] is True
        assert context["survey_config"]["type"] == "digcomp"
        assert "blocks_data" in context
        assert len(context["blocks_data"]) == 5

    def test_riasec_context(self, user, riasec_category, riasec_result):
        """Тест контекста для RIASEC"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )
        handler = UnifiedSurveyHandler(riasec_category, session)

        context = handler.get_results_context(riasec_result)
        assert context["is_unified"] is True
        assert context["survey_config"]["type"] == "riasec"
        assert "blocks_data_sorted" in context
        assert len(context["blocks_data"]) == 6

    def test_user_type_in_context(self, user, digcomp_category, digcomp_result):
        """Тест: тип пользователя в контексте"""
        user.user_type = "employee"
        user.save()

        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)

        context = handler.get_results_context(digcomp_result)
        assert context["user_type"] == "employee"
        assert context["user_type_color"] == "success"

    def test_important_notes_in_context(self, user, digcomp_category, digcomp_result):
        """Тест: важные замечания в контексте"""
        SurveyInterpretation.objects.create(
            survey_type="digcomp",
            code="common",
            user_type="common",
            title="Важные замечания",
            important_notes="<ul><li>Тестовое замечание</li></ul>",
            is_active=True,
        )

        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)

        context = handler.get_results_context(digcomp_result)
        assert "important_notes" in context


# ============================================================
# Тесты для get_default_recommendations
# ============================================================


@pytest.mark.django_db
class TestGetDefaultRecommendations:
    """Тесты стандартных рекомендаций"""

    def test_digcomp_employee(self, user, digcomp_category):
        """Тест рекомендаций DigComp для работника"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)
        rec = handler.get_default_recommendations("employee")
        assert "план развития" in rec

    def test_riasec_employer(self, user, riasec_category):
        """Тест рекомендаций RIASEC для работодателя"""
        session = SurveySession.objects.create(
            user=user, category=riasec_category, attempt=1
        )
        handler = UnifiedSurveyHandler(riasec_category, session)
        rec = handler.get_default_recommendations("employer")
        assert "подбора персонала" in rec

    def test_default_fallback(self, user, survey_category):
        """Тест fallback рекомендаций"""
        session = SurveySession.objects.create(
            user=user, category=survey_category, attempt=1
        )
        handler = UnifiedSurveyHandler(survey_category, session)
        rec = handler.get_default_recommendations("unknown")
        assert "планирования развития" in rec


# ============================================================
# Тесты для get_results_template
# ============================================================


@pytest.mark.django_db
class TestGetResultsTemplate:
    """Тесты получения шаблона результатов"""

    def test_template_name(self, user, digcomp_category):
        """Тест: возвращает правильное имя шаблона"""
        session = SurveySession.objects.create(
            user=user, category=digcomp_category, attempt=1
        )
        handler = UnifiedSurveyHandler(digcomp_category, session)
        assert handler.get_results_template() == "surveys/survey_results.html"


# ============================================================
# Тесты для can_handle
# ============================================================


@pytest.mark.django_db
class TestCanHandle:
    """Тесты определения, может ли обработчик обработать опрос"""

    def test_can_handle_any_survey(self, survey_category):
        """Тест: обрабатывает любые опросы"""
        assert UnifiedSurveyHandler.can_handle(survey_category) is True
