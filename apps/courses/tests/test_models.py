import pytest
from django.db import IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.courses.models import Course, Category

pytestmark = pytest.mark.django_db


class TestCategoryModel:
    """Тесты для модели Category"""

    def test_category_creation(self, category):
        """Тест создания категории"""
        assert category.name == "Искусственный интеллект"
        assert category.slug == "iskusstvennyj-intellekt"
        assert str(category) == "Искусственный интеллект"

    def test_category_slug_generation(self):
        """Тест генерации слага из кириллицы"""
        category = Category.objects.create(name="Машинное обучение")
        assert category.slug == "mashinnoe-obuchenie"

    def test_category_slug_unique_constraint(self):
        """Тест уникальности слага"""
        Category.objects.create(name="Тест", slug="test-slug")

        with pytest.raises(IntegrityError):
            Category.objects.create(name="Тест 2", slug="test-slug")

    def test_category_slug_auto_increment(self):
        """Тест автоматического увеличения слага при дубликате"""
        cat1 = Category.objects.create(name="Программирование")
        # Пытаемся создать категорию с таким же slug, но другим именем
        cat2 = Category.objects.create(name="Программирование 2")

        # Проверяем, что slug у второй категории отличается
        assert cat2.slug != cat1.slug

        # создаём категорию, slug которой уже существует
        cat1 = Category.objects.create(name="Тест", slug="test-slug")
        cat2 = Category.objects.create(name="Тест2")  # slug сгенерируется как "test2"
        assert cat2.slug == "test2"

    def test_category_long_name(self, category_with_long_name):
        """Тест категории с длинным названием"""
        assert (
            category_with_long_name.name
            == "Сквозные виды профессиональной деятельности в промышленности"
        )
        assert len(category_with_long_name.name) > 50
        assert category_with_long_name.slug is not None

    def test_category_verbose_names(self):
        """Тест правильности verbose_name"""
        category = Category.objects.create(name="Тест")
        assert category._meta.get_field("name").verbose_name == "Название"
        assert category._meta.get_field("slug").verbose_name == "Слаг"

    def test_category_ordering(self):
        """Тест порядка сортировки"""
        cat1 = Category.objects.create(name="Бета")
        cat2 = Category.objects.create(name="Альфа")
        cat3 = Category.objects.create(name="Гамма")

        categories = Category.objects.all()
        # Сортировка по умолчанию должна быть по id
        assert categories[0].name == "Бета"
        assert categories[1].name == "Альфа"
        assert categories[2].name == "Гамма"


class TestCourseModel:
    """Тесты для модели Course"""

    def test_course_creation(self, course, organization, category):
        """Тест создания курса"""
        assert course.title == "Python для анализа данных"
        assert course.organization == organization
        assert course.url == "https://example.com/course/1"
        assert not course.is_deleted
        assert course.deleted_at is None
        assert str(course) == "Python для анализа данных"

    def test_course_soft_delete(self, course):
        """Тест мягкого удаления курса"""
        assert not course.is_deleted
        assert course.deleted_at is None

        course.is_deleted = True
        course.deleted_at = timezone.now()
        course.save()

        deleted_course = Course.objects.get(id=course.id)
        assert deleted_course.is_deleted is True
        assert deleted_course.deleted_at is not None

    def test_course_restore(self, deleted_course):
        """Тест восстановления курса"""
        assert deleted_course.is_deleted is True

        deleted_course.is_deleted = False
        deleted_course.deleted_at = None
        deleted_course.save()

        restored_course = Course.objects.get(id=deleted_course.id)
        assert restored_course.is_deleted is False
        assert restored_course.deleted_at is None

    def test_course_organization_relation(self, course, organization):
        """Тест связи с организацией"""
        assert course.organization == organization
        assert organization.courses.count() == 1
        assert organization.courses.first() == course

    def test_course_categories_m2m(self, course, category, another_category):
        """Тест связи многие-ко-многим с категориями"""
        assert course.categories.count() == 1
        assert category in course.categories.all()

        # Добавляем ещё одну категорию
        course.categories.add(another_category)
        assert course.categories.count() == 2
        assert another_category in course.categories.all()

    def test_course_multiple_categories(self, course_with_multiple_categories):
        """Тест курса с несколькими категориями"""
        assert course_with_multiple_categories.categories.count() == 3
        names = [cat.name for cat in course_with_multiple_categories.categories.all()]
        assert "Искусственный интеллект" in names
        assert "Машинное обучение" in names
        assert "Информационные технологии" in names

    def test_course_url_unique_constraint(self, course, organization):
        """Тест уникальности URL курса"""
        with pytest.raises(IntegrityError):
            Course.objects.create(
                title="Другой курс",
                description="Описание",
                organization=organization,
                url=course.url,  # Тот же URL
            )

    def test_course_fields_optional(self, organization):
        """Тест опциональных полей (могут быть пустыми)"""
        course = Course.objects.create(
            title="Минимальный курс",
            organization=organization,
            url="https://example.com/course/minimal",
        )

        assert course.description == ""
        assert course.program_type == ""
        assert course.duration_hours is None
        assert course.duration_weeks is None
        assert course.price == ""

    def test_course_with_all_fields(self, course_with_all_fields):
        """Тест курса со всеми заполненными полями"""
        assert course_with_all_fields.title == "Полный курс со всеми полями"
        assert course_with_all_fields.duration_hours == 120
        assert course_with_all_fields.program_type == "Повышение квалификации"
        assert course_with_all_fields.teachers == "Петров П.П., Сидоров С.С."
        assert course_with_all_fields.price == "50000"

    def test_course_default_ordering(self, organization):
        """Тест сортировки по умолчанию (по id DESC)"""
        course1 = Course.objects.create(
            title="Курс 1",
            organization=organization,
            url="https://example.com/course/1",
        )
        course2 = Course.objects.create(
            title="Курс 2",
            organization=organization,
            url="https://example.com/course/2",
        )

        courses = Course.objects.all()
        assert courses[0].id > courses[1].id

    def test_course_last_parsed_auto_now(self, course):
        """Тест автообновления даты парсинга"""
        old_date = course.last_parsed
        course.save()
        # При сохранении дата должна обновиться
        assert course.last_parsed != old_date

    def test_course_filter_active(self, course, deleted_course):
        """Тест фильтрации активных курсов"""
        active_courses = Course.objects.filter(is_deleted=False)
        assert active_courses.count() == 1
        assert course in active_courses
        assert deleted_course not in active_courses

    def test_course_filter_deleted(self, course, deleted_course):
        """Тест фильтрации удалённых курсов"""
        deleted_courses = Course.objects.filter(is_deleted=True)
        assert deleted_courses.count() == 1
        assert deleted_course in deleted_courses
        assert course not in deleted_courses

    def test_course_organization_courses_count(
        self, organization, course, deleted_course
    ):
        """Тест подсчёта курсов организации"""
        # Учитывая, что deleted_course тоже принадлежит организации
        assert organization.courses.count() == 2
        assert organization.courses.filter(is_deleted=False).count() == 1


class TestCourseConstraints:
    """Тесты ограничений модели Course"""

    def test_course_requires_title(self, organization):
        """Тест обязательности названия"""
        course = Course(
            title="",  # Пустое название
            organization=organization,
            url="https://example.com/course/1",
        )

        # Проверяем валидацию
        with pytest.raises(ValidationError):
            course.full_clean()

    def test_course_requires_organization(self):
        """Тест обязательности организации"""
        with pytest.raises(IntegrityError):
            Course.objects.create(
                title="Курс без организации", url="https://example.com/course/no-org"
            )

    def test_course_requires_url(self, organization):
        """Тест обязательности URL"""
        course = Course(
            title="Тестовый курс", organization=organization, url=""  # Пустой URL
        )

        with pytest.raises(ValidationError):
            course.full_clean()

    def test_duration_hours_positive(self, organization):
        """Тест положительности количества часов"""
        course = Course.objects.create(
            title="Курс",
            organization=organization,
            url="https://example.com/course/positive",
            duration_hours=100,  # Положительное число
        )
        assert course.duration_hours == 100
