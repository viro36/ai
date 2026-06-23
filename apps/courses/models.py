from django.db import models
from django.utils.text import slugify
from transliterate import translit
from apps.organizations.models import Organization


class Course(models.Model):
    """
    Модель курса (образовательной программы)
    """

    # Основная информация
    title = models.CharField(max_length=500, verbose_name="Название курса")
    description = models.TextField(blank=True, verbose_name="Описание")

    # Ссылка на организацию (вуз/провайдер)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Организация",
    )

    # Категории / направления
    categories = models.ManyToManyField(
        "Category", blank=True, verbose_name="Категории"
    )

    # Атрибуты курса
    program_type = models.CharField(
        max_length=200, blank=True, verbose_name="Тип программы"
    )
    duration_hours = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Объём (часы)"
    )
    duration_weeks = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Продолжительность (недели)"
    )
    study_mode = models.CharField(
        max_length=100, blank=True, verbose_name="Режим обучения"
    )
    format = models.CharField(max_length=100, blank=True, verbose_name="Форма обучения")
    teachers = models.TextField(blank=True, verbose_name="Преподаватели")
    target_audience = models.TextField(blank=True, verbose_name="Целевая аудитория")
    topics = models.TextField(blank=True, verbose_name="Содержание программы")

    start_dates = models.CharField(
        max_length=200, blank=True, verbose_name="Даты начала обучения"
    )
    price = models.CharField(max_length=100, blank=True, verbose_name="Стоимость")
    field_of_study = models.CharField(
        max_length=500, blank=True, verbose_name="Направление (из карточки)"
    )

    document_type = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Выдаваемый документ"
    )

    # Ссылка на страницу курса на сайте вуза
    url = models.URLField(verbose_name="Ссылка на курс", unique=True, max_length=500)

    # Дата парсинга (для обновлений)
    last_parsed = models.DateTimeField(auto_now=True, verbose_name="Дата добавления")

    # Для мягкого удаления
    is_deleted = models.BooleanField(default=False, verbose_name="Удалён")
    deleted_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Дата удаления"
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=250, unique=True, verbose_name="Название")
    slug = models.SlugField(
        max_length=250, unique=True, blank=True, verbose_name="Слаг"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            # Транслитерируем кириллицу в латиницу
            latin_name = translit(self.name, "ru", reversed=True)
            self.slug = slugify(latin_name)

            # Если slug всё равно пустой, используем имя с заменой символов
            if not self.slug:
                import re

                self.slug = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")

            # Проверяем уникальность
            original_slug = self.slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name
