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

    order = models.PositiveIntegerField(unique=True, verbose_name="Порядковый номер")
    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="textarea",
        verbose_name="Тип вопроса",
    )
    options = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Варианты ответов",
        help_text='JSON массив с вариантами, например: ["Автоматизация", "Внедрение ИИ"]',
    )
    is_required = models.BooleanField(default=True, verbose_name="Обязательный")
    placeholder = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Подсказка (placeholder)"
    )
    help_text = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Пояснение к вопросу"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
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


class RequirementStatus(models.Model):
    """Модель статусов технического задания"""

    code = models.PositiveSmallIntegerField(unique=True, verbose_name="Код статуса")
    name = models.CharField(max_length=100, verbose_name="Название статуса")
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание статуса"
    )
    color = models.CharField(
        max_length=20,
        default="#6c757d",
        verbose_name="Цвет (HEX)",
        help_text="Например: #28a745, #dc3545, #17a2b8",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveSmallIntegerField(
        default=0, verbose_name="Порядок сортировки"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Статус технического задания"
        verbose_name_plural = "Статусы технических заданий"
        ordering = ["order", "code"]

    def __str__(self):
        return self.name


class TechnicalRequirement(models.Model):
    """Форма технического задания на разработку образовательного продукта"""

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technical_requirements",
        verbose_name="Работодатель",
    )

    answers = models.JSONField(
        default=dict,
        verbose_name="Ответы на вопросы",
        help_text='Формат: {"question_id": "answer"}',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Техническое задание"
        verbose_name_plural = "Технические задания"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ТЗ #{self.id} от {self.employer.get_full_name()}"

    def get_answer(self, question_id):
        """Получить ответ на конкретный вопрос"""
        return self.answers.get(str(question_id), "")


class TechnicalRequirementUniversity(models.Model):
    """Связь ТЗ с ВУЗом и статус"""

    technical_requirement = models.ForeignKey(
        TechnicalRequirement,
        on_delete=models.CASCADE,
        related_name="university_statuses",
        verbose_name="Техническое задание",
    )
    university = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="requirement_statuses",
        verbose_name="ВУЗ",
        limit_choices_to={"users__user_type": "university"},
    )
    status = models.ForeignKey(
        RequirementStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requirement_universities",
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Статус ТЗ для ВУЗа"
        verbose_name_plural = "Статусы ТЗ для ВУЗов"
        unique_together = ["technical_requirement", "university"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"ТЗ #{self.technical_requirement.id} - {self.university.short_name}: {self.status}"
