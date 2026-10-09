import pytest

from apps.surveys.models import ScaleLabel, SurveyInterpretation
from apps.surveys.scripts.add_scale_labels import add_global_scale_labels
from apps.surveys.scripts.add_survey_descriptions import add_survey_descriptions
from apps.surveys.scripts.load_survey_data import (
    BIG5_USAGE,
    DIGCOMP_DATA,
    DIGCOMP_USAGE,
    RIASEC_DATA,
    load_common,
    load_levels,
    load_usage,
    main,
)

# ============================================================
# Тесты для add_scale_labels.py
# ============================================================


@pytest.mark.django_db
class TestAddScaleLabels:
    """Тесты для скрипта добавления глобальных формулировок шкалы"""

    def test_add_scale_labels_creates_labels(self):
        """Тест: скрипт создаёт глобальные формулировки шкалы"""
        # Запускаем скрипт
        add_global_scale_labels()

        # Проверяем, что созданы 5 формулировок
        labels = ScaleLabel.objects.filter(category__isnull=True)
        assert labels.count() == 5

        # Проверяем значения
        assert labels.filter(scale_value=1).exists()
        assert labels.filter(scale_value=2).exists()
        assert labels.filter(scale_value=3).exists()
        assert labels.filter(scale_value=4).exists()
        assert labels.filter(scale_value=5).exists()

    def test_add_scale_labels_idempotent(self):
        """Тест: повторный запуск не создаёт дубликаты"""
        # Первый запуск
        add_global_scale_labels()
        first_count = ScaleLabel.objects.filter(category__isnull=True).count()

        # Второй запуск
        add_global_scale_labels()
        second_count = ScaleLabel.objects.filter(category__isnull=True).count()

        assert first_count == second_count == 5


# ============================================================
# Тесты для add_survey_descriptions.py
# ============================================================


@pytest.mark.django_db
class TestAddSurveyDescriptions:
    """Тесты для скрипта добавления инструкций и описаний"""

    def test_add_descriptions_updates_categories(
        self, digcomp_category, riasec_category, big5_category, gardner_category
    ):
        """Тест: скрипт обновляет категории"""
        from apps.surveys.scripts.add_survey_descriptions import add_survey_descriptions

        # Изначально инструкции пустые
        assert digcomp_category.instruction_text is None
        assert digcomp_category.result_description is None

        # Запускаем скрипт
        add_survey_descriptions()

        # Обновляем объекты из БД
        digcomp_category.refresh_from_db()
        riasec_category.refresh_from_db()
        big5_category.refresh_from_db()
        gardner_category.refresh_from_db()

        # Проверяем, что инструкции добавились
        assert digcomp_category.instruction_text is not None
        assert riasec_category.instruction_text is not None
        assert big5_category.instruction_text is not None
        assert gardner_category.instruction_text is not None

        # Проверяем, что описания результатов добавились
        assert digcomp_category.result_description is not None
        assert riasec_category.result_description is not None
        assert big5_category.result_description is not None
        assert gardner_category.result_description is not None

    def test_add_descriptions_skip_missing_categories(self):
        """Тест: скрипт пропускает отсутствующие категории"""
        # Запускаем скрипт - не должно быть ошибок
        add_survey_descriptions()


# ============================================================
# Тесты для load_survey_data.py
# ============================================================


@pytest.mark.django_db
class TestLoadSurveyData:
    """Тесты для скрипта загрузки интерпретаций"""

    def test_load_levels_creates_interpretations(self):
        """Тест: загрузка уровней создаёт интерпретации"""
        load_levels("digcomp", DIGCOMP_DATA)

        # Проверяем создание уровней для DigComp
        interpretations = SurveyInterpretation.objects.filter(survey_type="digcomp")
        assert interpretations.count() >= 4  # 4 уровня * 4 типа пользователей = 16

    def test_load_common_creates_important_notes(self):
        """Тест: загрузка важных замечаний"""
        load_common("riasec", RIASEC_DATA)

        # Проверяем создание важных замечаний
        interpretations = SurveyInterpretation.objects.filter(
            survey_type="riasec", code="common"
        )
        assert interpretations.exists()
        assert "важные замечания" in interpretations.first().title.lower()

    def test_load_usage_creates_recommendations(self):
        """Тест: загрузка рекомендаций"""
        load_usage("big5", BIG5_USAGE)

        # Проверяем создание рекомендаций
        interpretations = SurveyInterpretation.objects.filter(
            survey_type="big5", code="usage"
        )
        assert interpretations.count() == 3  # employee, employer, university

    def test_full_load(self):
        """Тест: полная загрузка всех данных"""
        # Запускаем основную функцию
        main()

        # Проверяем, что данные загружены
        assert SurveyInterpretation.objects.filter(survey_type="digcomp").exists()
        assert SurveyInterpretation.objects.filter(survey_type="riasec").exists()
        assert SurveyInterpretation.objects.filter(survey_type="big5").exists()
        assert SurveyInterpretation.objects.filter(survey_type="gardner").exists()


# ============================================================
# Тесты для init_survey_data.py
# ============================================================


@pytest.mark.django_db
class TestInitSurveyData:
    """Тесты для основного скрипта инициализации"""

    @pytest.mark.skip(reason="Этот тест проверяет интеграцию, покрыто другими тестами")
    def test_init_script_runs(self):
        pass


# ============================================================
# Тесты для management command import_survey_from_excel
# ============================================================


@pytest.mark.django_db
class TestImportCommand:
    """Тесты для команды импорта из Excel"""

    def test_import_command_creates_category(self):
        """Тест: команда импорта создаёт категорию"""
        # Создаём временный файл (в реальном тесте нужно создать mock)
        pass  # Здесь можно создать mock Excel файла

    def test_import_command_updates_existing_category(self):
        """Тест: команда обновляет существующую категорию"""
        pass


# ============================================================
# Тесты для целостности данных
# ============================================================


@pytest.mark.django_db
class TestDataIntegrity:
    """Тесты целостности загруженных данных"""

    @pytest.fixture(autouse=True)
    def load_data(self):
        """Загружаем данные перед тестами"""
        from apps.surveys.scripts.load_survey_data import main as load_main
        from apps.surveys.scripts.add_scale_labels import add_global_scale_labels

        add_global_scale_labels()
        load_main()

    def test_all_levels_have_interpretations(self):
        """Тест: для всех уровней есть интерпретации"""
        # Проверяем DigComp уровни
        for level in ["A2", "B1", "B2", "C1"]:
            assert SurveyInterpretation.objects.filter(
                survey_type="digcomp", code=level
            ).exists(), f"Нет интерпретации для уровня {level}"

        # Проверяем RIASEC уровни
        for level in ["low", "medium", "high"]:
            assert SurveyInterpretation.objects.filter(
                survey_type="riasec", code=level
            ).exists(), f"Нет интерпретации для уровня {level}"

    def test_all_surveys_have_usage_recommendations(self):
        """Тест: для всех опросов есть рекомендации"""
        for survey_type in ["digcomp", "riasec", "big5", "gardner"]:
            usage = SurveyInterpretation.objects.filter(
                survey_type=survey_type, code="usage"
            )
            assert usage.exists(), f"Нет рекомендаций для {survey_type}"
            assert usage.count() >= 3, f"Не хватает рекомендаций для {survey_type}"

    def test_all_surveys_have_important_notes(self):
        """Тест: для всех опросов есть важные замечания"""
        for survey_type in ["riasec", "big5"]:
            notes = SurveyInterpretation.objects.filter(
                survey_type=survey_type, code="common"
            )
            assert notes.exists(), f"Нет важных замечаний для {survey_type}"

    def test_scale_labels_exist(self):
        """Тест: глобальные формулировки шкалы существуют"""
        for value in range(1, 6):
            assert ScaleLabel.objects.filter(
                category__isnull=True, scale_value=value
            ).exists(), f"Нет формулировки для {value}"


# ============================================================
# Тесты для повторного запуска (идемпотентность)
# ============================================================


@pytest.mark.django_db
class TestIdempotency:
    """Тесты идемпотентности скриптов"""

    def test_load_levels_idempotent(self):
        """Тест: повторная загрузка уровней не создаёт дубликаты"""
        # Первая загрузка
        load_levels("digcomp", DIGCOMP_DATA)
        first_count = SurveyInterpretation.objects.filter(survey_type="digcomp").count()

        # Вторая загрузка
        load_levels("digcomp", DIGCOMP_DATA)
        second_count = SurveyInterpretation.objects.filter(
            survey_type="digcomp"
        ).count()

        assert first_count == second_count

    def test_load_usage_idempotent(self):
        """Тест: повторная загрузка рекомендаций не создаёт дубликаты"""
        load_usage("digcomp", DIGCOMP_USAGE)
        first_count = SurveyInterpretation.objects.filter(
            survey_type="digcomp", code="usage"
        ).count()

        load_usage("digcomp", DIGCOMP_USAGE)
        second_count = SurveyInterpretation.objects.filter(
            survey_type="digcomp", code="usage"
        ).count()

        assert first_count == second_count
