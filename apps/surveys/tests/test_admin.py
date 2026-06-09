import pytest
from django.urls import reverse
from django.contrib.admin.sites import AdminSite

from apps.surveys.admin import (
    SurveyCategoryAdmin,
    SurveyBlockAdmin,
    SurveyQuestionAdmin,
    DigCompResultAdmin,
    RiasacResultAdmin,
    Big5ResultAdmin,
    GardnerResultAdmin,
)
from apps.surveys.models import (
    SurveyCategory,
    SurveyBlock,
    SurveyQuestion,
    DigCompResult,
    RiasacResult,
    Big5Result,
    GardnerResult,
)

# ============================================================
# Тесты для SurveyCategoryAdmin
# ============================================================


@pytest.mark.django_db
class TestSurveyCategoryAdmin:
    """Тесты для админки SurveyCategory"""

    def test_list_display(self, admin_client, survey_category):
        """Тест отображения списка"""
        url = reverse("admin:surveys_surveycategory_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert survey_category.name in response.content.decode()

    def test_blocks_count(self, admin_client, survey_category, survey_block):
        """Тест подсчёта блоков"""
        admin = SurveyCategoryAdmin(SurveyCategory, AdminSite())
        assert admin.blocks_count(survey_category) == 1

    def test_questions_count(
        self, admin_client, survey_category, survey_block, survey_question
    ):
        """Тест подсчёта вопросов"""
        admin = SurveyCategoryAdmin(SurveyCategory, AdminSite())
        assert admin.questions_count(survey_category) == 1

    def test_sessions_count(self, admin_client, survey_category, completed_session):
        """Тест подсчёта сессий"""
        admin = SurveyCategoryAdmin(SurveyCategory, AdminSite())
        assert admin.sessions_count(survey_category) == 1

    def test_import_excel_form(self, admin_client):
        """Тест формы импорта Excel"""
        url = reverse("admin:import_excel")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Excel файл" in response.content.decode()


# ============================================================
# Тесты для SurveyBlockAdmin
# ============================================================


@pytest.mark.django_db
class TestSurveyBlockAdmin:
    """Тесты для админки SurveyBlock"""

    def test_list_display(self, admin_client, survey_block):
        """Тест отображения списка"""
        url = reverse("admin:surveys_surveyblock_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert survey_block.title in response.content.decode()

    def test_questions_count(self, admin_client, survey_block, survey_question):
        """Тест подсчёта вопросов в блоке"""
        admin = SurveyBlockAdmin(SurveyBlock, AdminSite())
        assert admin.questions_count(survey_block) == 1

    def test_edit_permission(self, admin_client, survey_block):
        """Тест редактирования блока"""
        url = reverse("admin:surveys_surveyblock_change", args=[survey_block.id])
        response = admin_client.get(url)
        assert response.status_code == 200


# ============================================================
# Тесты для ScaleLabelAdmin
# ============================================================


@pytest.mark.django_db
class TestScaleLabelAdmin:
    """Тесты для админки ScaleLabel"""

    def test_list_display(self, admin_client, global_scale_labels):
        """Тест отображения списка"""
        url = reverse("admin:surveys_scalelabel_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_label(self, admin_client, global_scale_labels):
        """Тест редактирования формулировки"""
        label = global_scale_labels[0]
        url = reverse("admin:surveys_scalelabel_change", args=[label.id])
        response = admin_client.get(url)
        assert response.status_code == 200


# ============================================================
# Тесты для SurveyQuestionAdmin
# ============================================================


@pytest.mark.django_db
class TestSurveyQuestionAdmin:
    """Тесты для админки SurveyQuestion"""

    def test_list_display(self, admin_client, survey_question):
        """Тест отображения списка"""
        url = reverse("admin:surveys_surveyquestion_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_text_preview(self, admin_client, survey_question):
        """Тест предпросмотра текста вопроса"""
        admin = SurveyQuestionAdmin(SurveyQuestion, AdminSite())
        preview = admin.text_preview(survey_question)
        assert preview == survey_question.text

    def test_responses_count(self, admin_client, survey_question, survey_response):
        """Тест подсчёта ответов"""
        admin = SurveyQuestionAdmin(SurveyQuestion, AdminSite())
        assert admin.responses_count(survey_question) == 1


# ============================================================
# Тесты для SurveyInterpretationAdmin
# ============================================================


@pytest.mark.django_db
class TestSurveyInterpretationAdmin:
    """Тесты для админки SurveyInterpretation"""

    def test_list_display(self, admin_client, digcomp_interpretations):
        """Тест отображения списка"""
        url = reverse("admin:surveys_surveyinterpretation_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_create_interpretation(self, admin_client):
        """Тест создания интерпретации"""
        url = reverse("admin:surveys_surveyinterpretation_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_interpretation(self, admin_client, digcomp_interpretations):
        """Тест редактирования интерпретации"""
        interpretation = digcomp_interpretations[0]
        url = reverse(
            "admin:surveys_surveyinterpretation_change", args=[interpretation.id]
        )
        response = admin_client.get(url)
        assert response.status_code == 200


# ============================================================
# Тесты для DigCompResultAdmin
# ============================================================


@pytest.mark.django_db
class TestDigCompResultAdmin:
    """Тесты для админки DigCompResult"""

    def test_list_display(self, admin_client, digcomp_result):
        """Тест отображения списка"""
        url = reverse("admin:surveys_digcompresult_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_readonly_fields(self, admin_client, digcomp_result):
        """Тест чтения полей (только для чтения)"""
        admin = DigCompResultAdmin(DigCompResult, AdminSite())
        assert admin.has_add_permission(None) is False

    def test_detail_view(self, admin_client, digcomp_result):
        """Тест просмотра деталей"""
        url = reverse("admin:surveys_digcompresult_change", args=[digcomp_result.id])
        response = admin_client.get(url)
        assert response.status_code == 200


# ============================================================
# Тесты для RiasacResultAdmin
# ============================================================


@pytest.mark.django_db
class TestRiasacResultAdmin:
    """Тесты для админки RiasacResult"""

    def test_list_display(self, admin_client, riasec_result):
        """Тест отображения списка"""
        url = reverse("admin:surveys_riasacresult_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_readonly_fields(self, admin_client, riasec_result):
        """Тест чтения полей (только для чтения)"""
        admin = RiasacResultAdmin(RiasacResult, AdminSite())
        assert admin.has_add_permission(None) is False


# ============================================================
# Тесты для Big5ResultAdmin
# ============================================================


@pytest.mark.django_db
class TestBig5ResultAdmin:
    """Тесты для админки Big5Result"""

    def test_list_display(self, admin_client, big5_result):
        """Тест отображения списка"""
        url = reverse("admin:surveys_big5result_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_readonly_fields(self, admin_client, big5_result):
        """Тест чтения полей (только для чтения)"""
        admin = Big5ResultAdmin(Big5Result, AdminSite())
        assert admin.has_add_permission(None) is False


# ============================================================
# Тесты для GardnerResultAdmin
# ============================================================


@pytest.mark.django_db
class TestGardnerResultAdmin:
    """Тесты для админки GardnerResult"""

    def test_list_display(self, admin_client, gardner_result):
        """Тест отображения списка"""
        url = reverse("admin:surveys_gardnerresult_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_readonly_fields(self, admin_client, gardner_result):
        """Тест чтения полей (только для чтения)"""
        admin = GardnerResultAdmin(GardnerResult, AdminSite())
        assert admin.has_add_permission(None) is False


# ============================================================
# Тесты для доступов
# ============================================================


@pytest.mark.django_db
class TestAdminPermissions:
    """Тесты прав доступа к админке"""

    def test_admin_required_for_survey_category(self, client, user):
        """Тест: неавторизованный пользователь не может зайти в админку"""
        client.force_login(user)
        url = reverse("admin:surveys_surveycategory_changelist")
        response = client.get(url)
        # Обычный пользователь не имеет доступа к админке
        assert response.status_code == 302 or response.status_code == 403

    def test_superuser_access(self, admin_client, survey_category):
        """Тест: суперпользователь имеет доступ"""
        url = reverse("admin:surveys_surveycategory_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_custom_admin_has_module_permission(self, admin_client):
        """Тест: суперпользователь видит модуль опросов"""
        url = reverse("admin:index")
        response = admin_client.get(url)
        content = response.content.decode()
        assert "Опросы" in content or "surveys" in content.lower()


# ============================================================
# Тесты для inline моделей
# ============================================================


@pytest.mark.django_db
class TestInlines:
    """Тесты для inline форм"""

    def test_survey_block_inline(self, admin_client, survey_category):
        """Тест: блоки отображаются в категории"""
        url = reverse("admin:surveys_surveycategory_change", args=[survey_category.id])
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_survey_question_inline(self, admin_client, survey_block):
        """Тест: вопросы отображаются в блоке"""
        url = reverse("admin:surveys_surveyblock_change", args=[survey_block.id])
        response = admin_client.get(url)
        assert response.status_code == 200


# ============================================================
# Тесты для импорта Excel
# ============================================================


@pytest.mark.django_db
class TestExcelImport:
    """Тесты для импорта из Excel"""

    def test_import_excel_get_form(self, admin_client):
        """Тест: отображение формы импорта"""
        url = reverse("admin:import_excel")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Excel" in response.content.decode()

    def test_import_excel_post_no_file(self, admin_client):
        """Тест: отправка пустой формы"""
        url = reverse("admin:import_excel")
        response = admin_client.post(url, {})
        assert response.status_code == 200
        assert "Обязательное поле" in response.content.decode()
