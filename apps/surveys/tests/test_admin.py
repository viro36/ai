import pytest
from django.urls import reverse
from django.contrib.admin.sites import AdminSite

from apps.surveys.admin import (
    EducationProgramAdmin,
    GeneralizedLaborFunctionAdmin,
    ProfessionalStandardProgramAdmin,
    SurveyCategoryAdmin,
    SurveyBlockAdmin,
    SurveyQuestionAdmin,
    DigCompResultAdmin,
    RiasacResultAdmin,
    Big5ResultAdmin,
    GardnerResultAdmin,
)
from apps.surveys.models import (
    EducationProgram,
    GeneralizedLaborFunction,
    ProfessionalStandardProgram,
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


# ============================================================
# Тесты для RiasecCodeInterpretationAdmin
# ============================================================


@pytest.mark.django_db
class TestRiasecCodeInterpretationAdmin:
    """Тесты для админки RiasecCodeInterpretation"""

    def test_list_display(self, admin_client, riasec_code):
        """Список отображается"""
        url = reverse("admin:surveys_riaseccodeinterpretation_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "RIA" in response.content.decode()

    def test_create(self, admin_client):
        """Форма создания доступна"""
        url = reverse("admin:surveys_riaseccodeinterpretation_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit(self, admin_client, riasec_code):
        """Форма редактирования доступна"""
        url = reverse(
            "admin:surveys_riaseccodeinterpretation_change",
            args=[riasec_code.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_filter_by_dominant(self, admin_client, riasec_code):
        """Фильтр по доминирующему типу работает"""
        url = reverse("admin:surveys_riaseccodeinterpretation_changelist")
        response = admin_client.get(url, {"dominant": "R"})
        assert response.status_code == 200

    def test_search_by_professions(self, admin_client, riasec_code):
        """Поиск по профессиям работает"""
        url = reverse("admin:surveys_riaseccodeinterpretation_changelist")
        response = admin_client.get(url, {"q": "Инженер"})
        assert response.status_code == 200


# ============================================================
# Тесты для ProfessionalStandardAdmin
# ============================================================


@pytest.mark.django_db
class TestProfessionalStandardAdmin:
    """Тесты для админки ProfessionalStandard"""

    def test_list_display(self, admin_client, professional_standard):
        """Список отображается"""
        url = reverse("admin:surveys_professionalstandard_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "10.028" in response.content.decode()

    def test_create_form(self, admin_client):
        """Форма создания доступна"""
        url = reverse("admin:surveys_professionalstandard_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_form(self, admin_client, professional_standard):
        """Форма редактирования доступна"""
        url = reverse(
            "admin:surveys_professionalstandard_change",
            args=[professional_standard.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_filter_by_education_level(self, admin_client, professional_standard):
        """Фильтр по уровню образования работает"""
        url = reverse("admin:surveys_professionalstandard_changelist")
        response = admin_client.get(url, {"education_level": "VO"})
        assert response.status_code == 200

    def test_search_by_code(self, admin_client, professional_standard):
        """Поиск по коду работает"""
        url = reverse("admin:surveys_professionalstandard_changelist")
        response = admin_client.get(url, {"q": "10.028"})
        assert response.status_code == 200

    def test_riasec_codes_field_present(self, admin_client, professional_standard):
        """Поле riasec_codes присутствует в форме"""
        url = reverse(
            "admin:surveys_professionalstandard_change",
            args=[professional_standard.id],
        )
        response = admin_client.get(url)
        assert "riasec_codes" in response.content.decode()

    def test_otf_inline_present(self, admin_client, professional_standard):
        """Inline ОТФ присутствует в форме ПС"""
        url = reverse(
            "admin:surveys_professionalstandard_change",
            args=[professional_standard.id],
        )
        response = admin_client.get(url)
        content = response.content.decode()
        assert "labor_functions" in content or "Обобщённые трудовые функции" in content

    def test_program_inline_present(self, admin_client, professional_standard):
        """Inline связей с ФГОС присутствует в форме ПС"""
        url = reverse(
            "admin:surveys_professionalstandard_change",
            args=[professional_standard.id],
        )
        response = admin_client.get(url)
        content = response.content.decode()
        assert "program_links" in content or "education_program" in content


# ============================================================
# Тесты для GeneralizedLaborFunctionAdmin
# ============================================================


@pytest.mark.django_db
class TestGeneralizedLaborFunctionAdmin:
    """Тесты для админки GeneralizedLaborFunction"""

    def test_list_display(self, admin_client, professional_standard):
        """Список отображается"""
        otf = GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Разработка проектной документации",
            order=1,
        )
        url = reverse("admin:surveys_generalizedlaborfunction_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "A" in response.content.decode()

    def test_create_form(self, admin_client):
        """Форма создания доступна"""
        url = reverse("admin:surveys_generalizedlaborfunction_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_form(self, admin_client, professional_standard):
        """Форма редактирования доступна"""
        otf = GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Разработка",
            order=1,
        )
        url = reverse(
            "admin:surveys_generalizedlaborfunction_change",
            args=[otf.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_list_editable_order_and_is_active(
        self, admin_client, professional_standard
    ):
        """Поля order и is_active редактируются прямо в списке"""
        admin = GeneralizedLaborFunctionAdmin(GeneralizedLaborFunction, AdminSite())
        assert "order" in admin.list_editable
        assert "is_active" in admin.list_editable

    def test_filter_by_education_level(self, admin_client, professional_standard):
        """Фильтр по уровню образования ПС работает"""
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Разработка",
            order=1,
        )
        url = reverse("admin:surveys_generalizedlaborfunction_changelist")
        response = admin_client.get(
            url, {"professional_standard__education_level": "VO"}
        )
        assert response.status_code == 200


# ============================================================
# Тесты для EducationProgramAdmin
# ============================================================


@pytest.mark.django_db
class TestEducationProgramAdmin:
    """Тесты для админки EducationProgram"""

    def test_list_display(self, admin_client, education_program):
        """Список отображается"""
        url = reverse("admin:surveys_educationprogram_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "07.03.03" in response.content.decode()

    def test_create_form(self, admin_client):
        """Форма создания доступна"""
        url = reverse("admin:surveys_educationprogram_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_form(self, admin_client, education_program):
        """Форма редактирования доступна"""
        url = reverse(
            "admin:surveys_educationprogram_change",
            args=[education_program.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_filter_by_education_level(self, admin_client, education_program):
        """Фильтр по уровню образования работает"""
        url = reverse("admin:surveys_educationprogram_changelist")
        response = admin_client.get(url, {"education_level": "VO"})
        assert response.status_code == 200

    def test_search_by_code(self, admin_client, education_program):
        """Поиск по коду работает"""
        url = reverse("admin:surveys_educationprogram_changelist")
        response = admin_client.get(url, {"q": "07.03.03"})
        assert response.status_code == 200

    def test_list_editable_is_active(self):
        """Поле is_active редактируется прямо в списке"""
        admin = EducationProgramAdmin(EducationProgram, AdminSite())
        assert "is_active" in admin.list_editable


# ============================================================
# Тесты для ProfessionalStandardProgramAdmin
# ============================================================


@pytest.mark.django_db
class TestProfessionalStandardProgramAdmin:
    """Тесты для админки ProfessionalStandardProgram"""

    def test_list_display(self, admin_client, professional_standard, education_program):
        """Список отображается"""
        ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        url = reverse("admin:surveys_professionalstandardprogram_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_create_form(self, admin_client):
        """Форма создания доступна"""
        url = reverse("admin:surveys_professionalstandardprogram_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_edit_form(self, admin_client, professional_standard, education_program):
        """Форма редактирования доступна"""
        link = ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        url = reverse(
            "admin:surveys_professionalstandardprogram_change",
            args=[link.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_autocomplete_fields(self):
        """Поля autocomplete настроены"""
        admin = ProfessionalStandardProgramAdmin(
            ProfessionalStandardProgram, AdminSite()
        )
        assert "professional_standard" in admin.autocomplete_fields
        assert "education_program" in admin.autocomplete_fields

    def test_list_editable_order(self):
        """Поле order редактируется прямо в списке"""
        admin = ProfessionalStandardProgramAdmin(
            ProfessionalStandardProgram, AdminSite()
        )
        assert "order" in admin.list_editable
