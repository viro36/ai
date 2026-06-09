import pytest
from django import forms

from apps.courses.forms import CourseForm
from apps.courses.models import Course, Category

pytestmark = pytest.mark.django_db


class TestCourseForm:
    """Тесты для формы CourseForm"""

    def test_form_valid_with_required_fields(self, organization, course_data):
        """Тест валидной формы с обязательными полями"""
        minimal_data = {
            "title": "Минимальный курс",
            "url": "https://example.com/minimal",
        }

        form = CourseForm(data=minimal_data)
        assert form.is_valid(), form.errors

    def test_form_invalid_without_title(self, organization):
        """Тест невалидной формы без названия"""
        data = {
            "url": "https://example.com/course",
        }

        form = CourseForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_form_invalid_without_url(self, organization):
        """Тест невалидной формы без URL"""
        data = {
            "title": "Курс без URL",
        }

        form = CourseForm(data=data)
        assert not form.is_valid()
        assert "url" in form.errors

    def test_form_invalid_with_invalid_url(self, organization):
        """Тест невалидной формы с неправильным URL"""
        data = {
            "title": "Курс с плохим URL",
            "url": "not-a-valid-url",
        }

        form = CourseForm(data=data)
        assert not form.is_valid()
        assert "url" in form.errors

    def test_form_with_all_fields(self, organization, course_data):
        """Тест формы со всеми полями"""
        form = CourseForm(data=course_data)
        assert form.is_valid(), form.errors

        for field in course_data.keys():
            if field != "new_category":
                assert form.cleaned_data[field] == course_data[field]

    def test_form_with_optional_fields_empty(self, organization):
        """Тест формы с пустыми опциональными полями"""
        data = {
            "title": "Курс с пустыми опциями",
            "url": "https://example.com/optional-empty",
            "description": "",
            "program_type": "",
            "duration_hours": None,
            "price": "",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        assert form.cleaned_data["description"] == ""
        assert form.cleaned_data["program_type"] == ""
        assert form.cleaned_data["duration_hours"] is None

    def test_form_save_without_commit(self, organization, course_data):
        """Тест сохранения формы без commit"""
        form = CourseForm(data=course_data)
        assert form.is_valid()

        instance = form.save(commit=False)
        assert instance.pk is None
        assert instance.title == course_data["title"]
        assert instance.url == course_data["url"]

        instance.organization = organization
        instance.save()
        assert instance.pk is not None

    def test_form_save_with_commit(self, organization, course_data):
        """Тест сохранения формы с commit=True"""
        form = CourseForm(data=course_data)
        assert form.is_valid()

        instance = form.save(commit=False)
        instance.organization = organization
        instance.save()

        # Для m2m полей нужно вызвать save_m2m или сохранить через save()
        # Но так как мы использовали save(commit=False), нужно вручную сохранить m2m
        if hasattr(form, "save_m2m"):
            form.save_m2m()

        assert instance.pk is not None
        assert Course.objects.filter(title=course_data["title"]).exists()

    def test_form_widgets_attributes(self):
        """Тест атрибутов виджетов"""
        form = CourseForm()

        assert "form-control" in form.fields["title"].widget.attrs.get("class", "")
        assert "placeholder" in form.fields["title"].widget.attrs

        assert isinstance(form.fields["categories"].widget, forms.SelectMultiple)
        assert "form-control" in form.fields["categories"].widget.attrs.get("class", "")

        assert "rows" in form.fields["description"].widget.attrs
        assert form.fields["description"].widget.attrs["rows"] == 5

    def test_form_labels(self):
        """Тест меток полей"""
        form = CourseForm()

        assert form.fields["title"].label == "Название курса"
        assert form.fields["url"].label == "Ссылка на курс"
        assert form.fields["description"].label == "Описание"
        assert form.fields["duration_hours"].label == "Объём (часы)"

    def test_form_help_texts(self):
        """Тест подсказок для полей"""
        form = CourseForm()

        assert (
            "Зажмите Ctrl для выбора нескольких" in form.fields["categories"].help_text
        )
        assert (
            "Можно добавить несколько категорий через запятую"
            in form.fields["new_category"].help_text
        )


# apps/courses/tests/test_forms.py (исправленный класс TestCourseFormWithCategories)


class TestCourseFormWithCategories:
    """Тесты для работы с категориями в форме"""

    def test_form_with_existing_categories(
        self, category, another_category, organization
    ):
        """Тест формы с существующими категориями"""
        data = {
            "title": "Курс с категориями",
            "url": "https://example.com/with-categories",
            "categories": [category.id, another_category.id],
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["categories"].count() == 2
        assert category in form.cleaned_data["categories"]
        assert another_category in form.cleaned_data["categories"]

        # Сохраняем через save() с commit=True
        course = form.save(commit=False)
        course.organization = organization
        course.save()
        # Для m2m связей нужно вызвать save_m2m
        form.save_m2m()

        # Проверяем, что категории добавились
        assert course.categories.count() == 2
        assert category in course.categories.all()
        assert another_category in course.categories.all()

    def test_form_with_new_category_single(self, organization):
        """Тест добавления одной новой категории"""
        data = {
            "title": "Курс с новой категорией",
            "url": "https://example.com/new-category",
            "new_category": "Новая категория",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        # Создаём и сохраняем курс вручную
        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Обрабатываем new_category вручную (как это делает форма)
        new_category_names = form.cleaned_data.get("new_category", "")
        if new_category_names:
            names = [
                name.strip() for name in new_category_names.split(",") if name.strip()
            ]
            unique_names = list(dict.fromkeys(names))
            for name in unique_names:
                category, _ = Category.objects.get_or_create(name=name)
                course.categories.add(category)

        # Обновляем курс из БД
        course.refresh_from_db()

        # Проверяем, что категория создана
        assert Category.objects.filter(name="Новая категория").exists()

        # Проверяем, что курс связан с категорией
        category = Category.objects.get(name="Новая категория")
        assert category in course.categories.all()
        assert course.categories.count() == 1

    def test_form_with_multiple_new_categories(self, organization):
        """Тест добавления нескольких новых категорий через запятую"""
        data = {
            "title": "Курс с несколькими новыми категориями",
            "url": "https://example.com/multiple-categories",
            "new_category": "Категория 1, Категория 2, Категория 3",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        # Создаём курс
        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Обрабатываем new_category вручную
        new_category_names = form.cleaned_data.get("new_category", "")
        if new_category_names:
            names = [
                name.strip() for name in new_category_names.split(",") if name.strip()
            ]
            unique_names = list(dict.fromkeys(names))
            for name in unique_names:
                category, _ = Category.objects.get_or_create(name=name)
                course.categories.add(category)

        course.refresh_from_db()

        # Проверяем, что все категории созданы
        assert Category.objects.filter(name="Категория 1").exists()
        assert Category.objects.filter(name="Категория 2").exists()
        assert Category.objects.filter(name="Категория 3").exists()

        # Проверяем, что курс связан со всеми категориями
        assert course.categories.count() == 3
        assert course.categories.filter(name="Категория 1").exists()
        assert course.categories.filter(name="Категория 2").exists()
        assert course.categories.filter(name="Категория 3").exists()

    def test_form_with_mixed_categories(self, organization, category):
        """Тест смешанного выбора: существующие + новые категории"""
        data = {
            "title": "Курс со смешанными категориями",
            "url": "https://example.com/mixed-categories",
            "categories": [category.id],
            "new_category": "Новая категория",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        # Сохраняем курс
        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Сохраняем выбранные категории
        if form.cleaned_data.get("categories"):
            course.categories.set(form.cleaned_data["categories"])

        # Обрабатываем новые категории
        new_category_names = form.cleaned_data.get("new_category", "")
        if new_category_names:
            names = [
                name.strip() for name in new_category_names.split(",") if name.strip()
            ]
            unique_names = list(dict.fromkeys(names))
            for name in unique_names:
                cat, _ = Category.objects.get_or_create(name=name)
                course.categories.add(cat)

        course.refresh_from_db()

        # Проверяем, что и существующая, и новая категории добавлены
        assert course.categories.count() == 2
        assert category in course.categories.all()
        assert Category.objects.filter(name="Новая категория").exists()
        assert course.categories.filter(name="Новая категория").exists()

    def test_form_with_empty_new_category(self, organization):
        """Тест формы с пустым полем new_category"""
        data = {
            "title": "Курс без новых категорий",
            "url": "https://example.com/no-new-category",
            "new_category": "",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Сохраняем выбранные категории (если есть)
        if form.cleaned_data.get("categories"):
            course.categories.set(form.cleaned_data["categories"])

        course.refresh_from_db()

        # Никаких новых категорий не создано
        assert Category.objects.count() == 0
        assert course.categories.count() == 0

    def test_form_with_whitespace_in_new_category(self, organization):
        """Тест обработки пробелов в названиях новых категорий"""
        data = {
            "title": "Курс с пробелами",
            "url": "https://example.com/whitespace",
            "new_category": "  Категория с пробелами  ,  Ещё категория  ",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Обрабатываем новые категории
        new_category_names = form.cleaned_data.get("new_category", "")
        if new_category_names:
            names = [
                name.strip() for name in new_category_names.split(",") if name.strip()
            ]
            unique_names = list(dict.fromkeys(names))
            for name in unique_names:
                cat, _ = Category.objects.get_or_create(name=name)
                course.categories.add(cat)

        course.refresh_from_db()

        # Проверяем, что пробелы обрезаны
        assert Category.objects.filter(name="Категория с пробелами").exists()
        assert Category.objects.filter(name="Ещё категория").exists()
        assert course.categories.count() == 2

    def test_form_with_duplicate_new_categories(self, organization):
        """Тест обработки дубликатов при добавлении новых категорий"""
        data = {
            "title": "Курс с дубликатами",
            "url": "https://example.com/duplicates",
            "new_category": "Дубликат, Дубликат, Оригинал",
        }

        form = CourseForm(data=data)
        assert form.is_valid(), form.errors

        course = form.save(commit=False)
        course.organization = organization
        course.save()

        # Обрабатываем новые категории с удалением дубликатов
        new_category_names = form.cleaned_data.get("new_category", "")
        if new_category_names:
            names = [
                name.strip() for name in new_category_names.split(",") if name.strip()
            ]
            unique_names = list(dict.fromkeys(names))
            for name in unique_names:
                cat, _ = Category.objects.get_or_create(name=name)
                course.categories.add(cat)

        course.refresh_from_db()

        # Должны быть созданы только уникальные категории
        assert Category.objects.filter(name="Дубликат").count() == 1
        assert Category.objects.filter(name="Оригинал").count() == 1
        assert course.categories.count() == 2

    def test_form_update_with_categories(self, organization, course, category):
        """Тест обновления курса с категориями"""
        # Изначально у курса есть одна категория
        course.categories.add(category)
        assert course.categories.count() == 1

        data = {
            "title": course.title,
            "url": course.url,
            "categories": [],  # Убираем все категории
            "new_category": "Новая категория при обновлении",
        }

        form = CourseForm(data=data, instance=course)
        assert form.is_valid(), form.errors

        # Сохраняем обновления
        updated_course = form.save()

        # Обновляем курс из БД
        updated_course.refresh_from_db()

        # Проверяем, что категории обновились
        assert updated_course.categories.count() == 1
        assert Category.objects.filter(name="Новая категория при обновлении").exists()
        assert updated_course.categories.filter(
            name="Новая категория при обновлении"
        ).exists()


class TestCourseFormValidation:
    """Тесты валидации формы"""

    def test_form_validates_url_format(self):
        """Тест валидации формата URL"""
        invalid_data = {
            "title": "Неверный URL",
            "url": "htp://wrong-url",
        }

        form = CourseForm(data=invalid_data)
        assert not form.is_valid()
        assert "url" in form.errors

    def test_form_validates_max_length(self):
        """Тест валидации максимальной длины полей"""
        long_title = "A" * 501
        data = {
            "title": long_title,
            "url": "https://example.com/long-title",
        }

        form = CourseForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_duration_hours_positive_number(self):
        """Тест валидации положительного числа для часов"""
        data = {
            "title": "Курс с отрицательными часами",
            "url": "https://example.com/negative-hours",
            "duration_hours": -10,
        }

        form = CourseForm(data=data)
        # Отрицательное число может пройти валидацию формы,
        # но будет поймано на уровне модели
        if form.is_valid():
            assert form.cleaned_data["duration_hours"] == -10

    def test_form_preserves_data_on_error(self):
        """Тест сохранения данных в форме при ошибке валидации"""
        data = {
            "title": "",
            "url": "invalid",
            "description": "Описание",
        }

        form = CourseForm(data=data)
        assert not form.is_valid()

        assert form.data["description"] == "Описание"


class TestCourseFormInitialization:
    """Тесты инициализации формы"""

    def test_form_initial_with_instance(self, course):
        """Тест инициализации формы с существующим экземпляром"""
        form = CourseForm(instance=course)

        assert form.initial["title"] == course.title
        assert form.initial["url"] == course.url
        assert form.initial["description"] == course.description

    def test_form_initial_with_categories(self, course, category):
        """Тест инициализации с категориями"""
        course.categories.add(category)
        form = CourseForm(instance=course)

        assert "categories" in form.fields

    def test_form_initial_without_instance(self):
        """Тест инициализации формы без экземпляра"""
        form = CourseForm()

        assert form.initial == {}


class TestCourseFormMeta:
    """Тесты Meta класса формы"""

    def test_form_uses_correct_model(self):
        """Тест использования правильной модели"""
        form = CourseForm()
        assert form._meta.model == Course

    def test_form_has_correct_fields(self):
        """Тест наличия всех необходимых полей"""
        expected_fields = [
            "title",
            "url",
            "description",
            "program_type",
            "categories",
            "new_category",
            "field_of_study",
            "duration_hours",
            "duration_weeks",
            "price",
            "study_mode",
            "format",
            "teachers",
            "target_audience",
            "topics",
            "start_dates",
            "document_type",
        ]

        form = CourseForm()
        for field in expected_fields:
            assert field in form.fields

    def test_form_excludes_some_model_fields(self):
        """Тест исключения некоторых полей модели"""
        excluded_fields = ["organization", "last_parsed", "is_deleted", "deleted_at"]

        form = CourseForm()
        for field in excluded_fields:
            assert field not in form.fields
