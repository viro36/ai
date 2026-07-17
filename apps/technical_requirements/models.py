from django.db import models
from django.conf import settings
from apps.organizations.models import Organization


class Question(models.Model):
    """Модель для хранения вопросов формы технического задания"""

    QUESTION_TYPES = [
        ("text", "Текстовое поле"),
        ("textarea", "Многострочное текстовое поле"),
        ("choice", "Выбор из вариантов"),
        ("multiple_choice", "Множественный выбор"),
        ("boolean", "Да/Нет"),
        ("date", "Дата"),
        ("number", "Число"),
    ]

    # Порядковый номер вопроса (1, 2, 3, ...)
    order = models.PositiveIntegerField(unique=True, verbose_name="Порядковый номер")

    # Текст вопроса
    text = models.TextField(verbose_name="Текст вопроса")

    # Тип вопроса
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="textarea",
        verbose_name="Тип вопроса",
    )

    # Для вопросов с выбором вариантов (choice, multiple_choice)
    options = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Варианты ответов",
        help_text='JSON массив с вариантами, например: ["Автоматизация", "Внедрение ИИ"]',
    )

    # Дополнительные настройки
    is_required = models.BooleanField(default=True, verbose_name="Обязательный")
    placeholder = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Подсказка (placeholder)"
    )
    help_text = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Пояснение к вопросу"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # Для условного отображения (зависит от другого вопроса)
    depends_on = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Зависит от вопроса",
    )
    depends_value = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Значение для отображения"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.text[:50]}"


class TechnicalRequirement(models.Model):
    """Форма технического задания на разработку образовательного продукта"""

    STATUS_CHOICES = [
        ("draft", "Черновик"),
        ("sent", "Отправлено"),
        ("in_development", "В разработке"),
        ("completed", "Завершено"),
        ("rejected", "Отклонено"),
    ]

    # Связь с работодателем
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technical_requirements",
        verbose_name="Работодатель",
    )

    # ВУЗы, которым отправлено предложение
    universities = models.ManyToManyField(
        Organization,
        related_name="received_requirements",
        verbose_name="ВУЗы-получатели",
        limit_choices_to={"users__user_type": "university"},
    )

    # Ответы на вопросы (хранятся в JSON)
    answers = models.JSONField(
        default=dict,
        verbose_name="Ответы на вопросы",
        help_text='Формат: {"question_id": "answer"}',
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name="Статус",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Техническое задание"
        verbose_name_plural = "Технические задания"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ТЗ #{self.id} от {self.employer.get_full_name()}"

    @property
    def universities_count(self):
        return self.universities.count()

    def get_answer(self, question_id):
        """Получить ответ на конкретный вопрос"""
        return self.answers.get(str(question_id), "")
