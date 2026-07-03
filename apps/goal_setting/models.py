from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Question(models.Model):
    """Модель вопроса для целеполагания"""

    QUESTION_TYPES = [
        ("choice", "Выбор из вариантов"),
        ("text", "Текстовый ответ"),
        ("date_range", "Диапазон дат"),
        ("multiple_choice", "Множественный выбор"),
    ]

    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="choice",
        verbose_name="Тип вопроса",
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание/подсказка к вопросу"
    )
    is_required = models.BooleanField(default=True, verbose_name="Обязательный")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    max_length = models.PositiveIntegerField(
        default=500, verbose_name="Максимальная длина ответа (для текстовых полей)"
    )
    is_multiple = models.BooleanField(
        default=False, verbose_name="Множественный выбор (для choice)"
    )
    has_custom_option = models.BooleanField(
        default=False, verbose_name="Есть вариант 'Свой ответ'"
    )
    custom_option_label = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Текст для 'Свой ответ'",
        default="Свой вариант",
    )

    class Meta:
        verbose_name = "Вопрос целеполагания"
        verbose_name_plural = "Вопросы целеполагания"
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.text[:50]}..."


class QuestionOption(models.Model):
    """Варианты ответов для вопросов с выбором"""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="Вопрос",
    )
    value = models.CharField(max_length=500, verbose_name="Значение")
    label = models.CharField(max_length=500, verbose_name="Отображаемый текст")
    is_custom = models.BooleanField(
        default=False, verbose_name="Позволяет ввести свой вариант"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        ordering = ["order"]

    def __str__(self):
        return f"{self.question.text[:30]} - {self.label}"


class GoalSettingResponse(models.Model):
    """Ответ пользователя на вопрос целеполагания"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="goal_setting_responses",
        verbose_name="Пользователь",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Вопрос",
    )
    answer_text = models.TextField(
        blank=True, null=True, verbose_name="Текстовый ответ"
    )
    answer_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        verbose_name="Выбранный вариант",
    )
    answer_date_start = models.DateField(
        blank=True, null=True, verbose_name="Дата начала (для диапазона)"
    )
    answer_date_end = models.DateField(
        blank=True, null=True, verbose_name="Дата окончания (для диапазона)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ответ целеполагания"
        verbose_name_plural = "Ответы целеполагания"
        unique_together = ["user", "question"]

    def __str__(self):
        return f"{self.user} - {self.question.text[:30]}"
