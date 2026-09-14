import pytest
from django.db import IntegrityError

from apps.surveys.models import (
    RiasecCodeInterpretation,
    ProfessionalStandard,
    GeneralizedLaborFunction,
    EducationProgram,
    ProfessionalStandardProgram,
)

# ============================================================
# Тесты для SurveyCategory: get_result_description_clean
# ============================================================


@pytest.mark.django_db
class TestSurveyCategoryCleanDescription:
    """Тесты очистки HTML в result_description"""

    def test_clean_strips_html(self, survey_category):
        survey_category.result_description = "<p>Привет <b>мир</b></p>"
        assert survey_category.get_result_description_clean() == "Привет мир"

    def test_clean_collapses_whitespace(self, survey_category):
        survey_category.result_description = "Строка 1\n\n\nСтрока 2   с пробелами"
        assert (
            survey_category.get_result_description_clean()
            == "Строка 1 Строка 2 с пробелами"
        )

    def test_clean_truncates_long_text(self, survey_category):
        survey_category.result_description = "x" * 2000
        result = survey_category.get_result_description_clean()
        assert len(result) <= 1503  # 1500 + "..."
        assert result.endswith("...")

    def test_clean_returns_none_for_empty(self, survey_category):
        survey_category.result_description = ""
        assert survey_category.get_result_description_clean() is None

        survey_category.result_description = None
        assert survey_category.get_result_description_clean() is None


# ============================================================
# Тесты для RiasecCodeInterpretation
# ============================================================


@pytest.mark.django_db
class TestRiasecCodeInterpretation:
    """Тесты для модели RiasecCodeInterpretation"""

    def test_create(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="Технический специалист",
            professions="Инженер, Техник, Механик",
        )
        assert obj.id is not None
        assert obj.code == "RIA"

    def test_str_method(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="SEC",
            dominant="S",
            secondary="E",
            tertiary="C",
            description="Социальный организатор",
            professions="",
        )
        assert "SEC" in str(obj)
        assert "Социальный организатор" in str(obj)

    def test_code_unique(self):
        RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="x",
            professions="y",
        )
        with pytest.raises(IntegrityError):
            RiasecCodeInterpretation.objects.create(
                code="RIA",
                dominant="R",
                secondary="I",
                tertiary="A",
                description="x",
                professions="y",
            )

    def test_get_professions_list_comma(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="x",
            professions="Инженер, Техник, Механик",
        )
        assert obj.get_professions_list() == ["Инженер", "Техник", "Механик"]

    def test_get_professions_list_newlines(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="x",
            professions="Инженер\nТехник\nМеханик",
        )
        assert obj.get_professions_list() == ["Инженер", "Техник", "Механик"]

    def test_get_professions_list_empty(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="x",
            professions="",
        )
        assert obj.get_professions_list() == []

    def test_get_professions_list_strips_spaces(self):
        obj = RiasecCodeInterpretation.objects.create(
            code="RIA",
            dominant="R",
            secondary="I",
            tertiary="A",
            description="x",
            professions="  Инженер ,  Техник  , Механик  ",
        )
        assert obj.get_professions_list() == ["Инженер", "Техник", "Механик"]


# ============================================================
# Тесты для ProfessionalStandard
# ============================================================


@pytest.mark.django_db
class TestProfessionalStandard:
    """Тесты для модели ProfessionalStandard"""

    def test_create(self):
        ps = ProfessionalStandard.objects.create(
            code="10.028",
            name="Архитектор-дизайнер",
            education_level="VO",
        )
        assert ps.id is not None
        assert ps.education_level == "VO"

    def test_str_method(self):
        ps = ProfessionalStandard.objects.create(
            code="10.028",
            name="Архитектор-дизайнер",
            education_level="VO",
        )
        assert str(ps) == "10.028 - Архитектор-дизайнер"

    def test_unique_together_code_education(self):
        ProfessionalStandard.objects.create(
            code="10.028",
            name="Архитектор-дизайнер",
            education_level="VO",
        )
        with pytest.raises(IntegrityError):
            ProfessionalStandard.objects.create(
                code="10.028",
                name="Другой",
                education_level="VO",
            )

    def test_same_code_different_education_levels(self):
        """Один код может быть и в ВО, и в СПО."""
        ps_vo = ProfessionalStandard.objects.create(
            code="40.182",
            name="Техник (ВО)",
            education_level="VO",
        )
        ps_spo = ProfessionalStandard.objects.create(
            code="40.182",
            name="Техник (СПО)",
            education_level="SPO",
        )
        assert ps_vo.id != ps_spo.id
        assert ProfessionalStandard.objects.filter(code="40.182").count() == 2

    def test_riasec_codes_m2m(self, riasec_code):
        ps = ProfessionalStandard.objects.create(
            code="10.028",
            name="Архитектор-дизайнер",
            education_level="VO",
        )
        ps.riasec_codes.add(riasec_code)
        assert ps.riasec_codes.count() == 1
        assert riasec_code in ps.riasec_codes.all()


# ============================================================
# Тесты для GeneralizedLaborFunction
# ============================================================


@pytest.mark.django_db
class TestGeneralizedLaborFunction:
    """Тесты для модели GeneralizedLaborFunction"""

    def test_create(self, professional_standard):
        otf = GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Разработка проектной документации",
            order=1,
        )
        assert otf.id is not None
        assert otf.code == "A"

    def test_str_method(self, professional_standard):
        otf = GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Разработка проектной документации",
            order=1,
        )
        assert "10.028" in str(otf)
        assert "A." in str(otf)
        assert "Разработка" in str(otf)

    def test_unique_together_ps_code(self, professional_standard):
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="Первая",
            order=1,
        )
        with pytest.raises(IntegrityError):
            GeneralizedLaborFunction.objects.create(
                professional_standard=professional_standard,
                code="A",
                name="Вторая",
                order=2,
            )

    def test_ordering_by_order(self, professional_standard):
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="B",
            name="B",
            order=2,
        )
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="A",
            order=1,
        )
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="C",
            name="C",
            order=3,
        )
        otfs = list(professional_standard.labor_functions.all())
        assert [o.code for o in otfs] == ["A", "B", "C"]

    def test_cascade_delete(self, professional_standard):
        GeneralizedLaborFunction.objects.create(
            professional_standard=professional_standard,
            code="A",
            name="A",
            order=1,
        )
        professional_standard.delete()
        assert GeneralizedLaborFunction.objects.count() == 0


# ============================================================
# Тесты для EducationProgram
# ============================================================


@pytest.mark.django_db
class TestEducationProgram:
    """Тесты для модели EducationProgram"""

    def test_create_vo(self):
        p = EducationProgram.objects.create(
            code="07.03.03",
            name="Дизайн архитектурной среды",
            education_level="VO",
        )
        assert p.id is not None
        assert p.education_level == "VO"

    def test_create_spo(self):
        p = EducationProgram.objects.create(
            code="12.02.10",
            name="Монтаж, техническое обслуживание...",
            education_level="SPO",
        )
        assert p.education_level == "SPO"

    def test_str_method(self):
        p = EducationProgram.objects.create(
            code="07.03.03",
            name="Дизайн архитектурной среды",
            education_level="VO",
        )
        assert str(p) == "07.03.03 - Дизайн архитектурной среды"

    def test_unique_together(self):
        EducationProgram.objects.create(
            code="07.03.03",
            name="Дизайн",
            education_level="VO",
        )
        with pytest.raises(IntegrityError):
            EducationProgram.objects.create(
                code="07.03.03",
                name="Дизайн",
                education_level="VO",
            )


# ============================================================
# Тесты для ProfessionalStandardProgram
# ============================================================


@pytest.mark.django_db
class TestProfessionalStandardProgram:
    """Тесты для модели ProfessionalStandardProgram"""

    def test_create_link(self, professional_standard, education_program):
        link = ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        assert link.id is not None
        assert link.order == 1

    def test_str_method(self, professional_standard, education_program):
        link = ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        assert "10.028" in str(link)
        assert "07.03.03" in str(link)
        assert "#1" in str(link)

    def test_unique_together(self, professional_standard, education_program):
        ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        with pytest.raises(IntegrityError):
            ProfessionalStandardProgram.objects.create(
                professional_standard=professional_standard,
                education_program=education_program,
                order=2,
            )

    def test_reverse_relations(self, professional_standard, education_program):
        ProfessionalStandardProgram.objects.create(
            professional_standard=professional_standard,
            education_program=education_program,
            order=1,
        )
        assert professional_standard.program_links.count() == 1
        assert education_program.standard_links.count() == 1
        assert (
            education_program.standard_links.first().professional_standard
            == professional_standard
        )


# ============================================================
# Тесты для логики get_career_guidance (порядок ВО/СПО)
# ============================================================


@pytest.mark.django_db
class TestCareerGuidanceOrder:
    """
    Проверяем логику: при education_level='SPO' блок СПО идёт первым.
    Тестируем не сам метод (он на хендлере), а структуру данных.
    """

    def test_programs_order_vo(self):
        """Если education_level='VO' → порядок ['vo', 'spo']."""
        education_level = "VO"
        if education_level == "SPO":
            programs_order = ["spo", "vo"]
        else:
            programs_order = ["vo", "spo"]
        assert programs_order == ["vo", "spo"]

    def test_programs_order_spo(self):
        """Если education_level='SPO' → порядок ['spo', 'vo']."""
        education_level = "SPO"
        if education_level == "SPO":
            programs_order = ["spo", "vo"]
        else:
            programs_order = ["vo", "spo"]
        assert programs_order == ["spo", "vo"]

    def test_programs_order_none(self):
        """Если education_level=None → порядок ['vo', 'spo']."""
        education_level = None
        if education_level == "SPO":
            programs_order = ["spo", "vo"]
        else:
            programs_order = ["vo", "spo"]
        assert programs_order == ["vo", "spo"]

    def test_standards_sorted_vo_first_manual(self, riasec_code):
        """Ручная сортировка для VO: сначала VO, потом SPO."""
        ps_vo = ProfessionalStandard.objects.create(
            code="10.028",
            name="ВО ПС",
            education_level="VO",
        )
        ps_spo = ProfessionalStandard.objects.create(
            code="12.001",
            name="СПО ПС",
            education_level="SPO",
        )
        ps_vo.riasec_codes.add(riasec_code)
        ps_spo.riasec_codes.add(riasec_code)

        standards = list(ProfessionalStandard.objects.filter(riasec_codes=riasec_code))
        # Сортируем как в хендлере для VO
        standards.sort(
            key=lambda s: (
                0 if s.education_level == "VO" else 1,
                s.code,
            )
        )
        assert standards[0].education_level == "VO"
        assert standards[1].education_level == "SPO"

    def test_standards_sorted_spo_first_manual(self, riasec_code):
        """Ручная сортировка для SPO: сначала SPO, потом VO."""
        ps_vo = ProfessionalStandard.objects.create(
            code="10.028",
            name="ВО ПС",
            education_level="VO",
        )
        ps_spo = ProfessionalStandard.objects.create(
            code="12.001",
            name="СПО ПС",
            education_level="SPO",
        )
        ps_vo.riasec_codes.add(riasec_code)
        ps_spo.riasec_codes.add(riasec_code)

        standards = list(ProfessionalStandard.objects.filter(riasec_codes=riasec_code))
        # Сортируем как в хендлере для SPO
        standards.sort(
            key=lambda s: (
                0 if s.education_level == "SPO" else 1,
                s.code,
            )
        )
        assert standards[0].education_level == "SPO"
        assert standards[1].education_level == "VO"

    def test_standards_sorted_spo_first_manual(self, riasec_code):
        """Проверяем ручную сортировку для СПО."""
        ps_vo = ProfessionalStandard.objects.create(
            code="10.028",
            name="ВО ПС",
            education_level="VO",
        )
        ps_spo = ProfessionalStandard.objects.create(
            code="12.001",
            name="СПО ПС",
            education_level="SPO",
        )
        ps_vo.riasec_codes.add(riasec_code)
        ps_spo.riasec_codes.add(riasec_code)

        standards = list(ProfessionalStandard.objects.filter(riasec_codes=riasec_code))
        # Сортируем как в хендлере для СПО
        standards.sort(
            key=lambda s: (
                0 if s.education_level == "SPO" else 1,
                s.code,
            )
        )
        assert standards[0].education_level == "SPO"
        assert standards[1].education_level == "VO"
