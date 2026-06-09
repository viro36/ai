from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SurveyCategory(models.Model):
    """Категория опроса (название опроса)"""

    name = models.CharField(max_length=255, verbose_name="Название опроса")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    instruction_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="Инструкция для вопросов",
        help_text="Отображается под каждым вопросом мелким шрифтом",
    )
    result_description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание результатов",
        help_text="Отображается в результатах после графика (поддерживает HTML)",
    )

    class Meta:
        verbose_name = "Категория опроса"
        verbose_name_plural = "Категории опросов"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_questions_count(self):
        """Получить количество активных вопросов в опросе"""
        from .models import SurveyQuestion

        return SurveyQuestion.objects.filter(
            block__category=self, is_active=True
        ).count()

    def get_display_description(self):
        """Получить описание для отображения (без технической информации)"""
        if self.description and "Импортирован из Excel" in self.description:
            return "Пройдите опрос, чтобы оценить свои навыки"
        return self.description or "Пройдите опрос, чтобы оценить свои навыки"


class SurveyBlock(models.Model):
    """Блок вопросов (раздел опроса)"""

    category = models.ForeignKey(
        SurveyCategory,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Категория опроса",
    )
    title = models.CharField(max_length=255, verbose_name="Название блока")
    description = models.TextField(blank=True, null=True, verbose_name="Описание блока")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок блока")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Блок вопросов"
        verbose_name_plural = "Блоки вопросов"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.category.name} - {self.title}"


# apps/surveys/models.py - обновляем ScaleLabel


class ScaleLabel(models.Model):
    """Формулировки для каждого значения шкалы"""

    category = models.ForeignKey(
        SurveyCategory,
        on_delete=models.CASCADE,
        related_name="scale_labels",
        verbose_name="Опрос",
        null=True,
        blank=True,
    )
    scale_value = models.PositiveSmallIntegerField(verbose_name="Значение шкалы (1-5)")
    label = models.CharField(max_length=255, verbose_name="Формулировка ответа")

    class Meta:
        verbose_name = "Формулировка шкалы"
        verbose_name_plural = "Формулировки шкалы"
        ordering = ["category", "scale_value"]
        unique_together = ["category", "scale_value"]

    def __str__(self):
        if self.category:
            return f"{self.category.name} - {self.scale_value} — {self.label}"
        return f"Глобальная - {self.scale_value} — {self.label}"


class SurveyQuestion(models.Model):
    """Вопрос опроса"""

    block = models.ForeignKey(
        SurveyBlock,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Блок вопросов",
        default="",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    q_number = models.PositiveIntegerField(
        default=0, verbose_name="Номер вопроса в блоке"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Вопрос опроса"
        verbose_name_plural = "Вопросы опросов"
        ordering = ["block__order", "q_number", "id"]

    def __str__(self):
        return f"{self.block.title}: {self.text[:50]}"


class SurveySession(models.Model):
    """Сессия прохождения опроса пользователем"""

    STATUS_CHOICES = [
        ("in_progress", "В процессе"),
        ("completed", "Завершён"),
        ("abandoned", "Прерван"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="survey_sessions",
        verbose_name="Пользователь",
    )
    category = models.ForeignKey(
        SurveyCategory,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Категория опроса",
    )

    attempt = models.PositiveIntegerField(default=1, verbose_name="Номер попытки")

    current_block = models.ForeignKey(
        SurveyBlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Текущий блок",
    )
    current_question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Текущий вопрос",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="in_progress",
        verbose_name="Статус",
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начало")
    completed_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Завершение"
    )

    class Meta:
        verbose_name = "Сессия опроса"
        verbose_name_plural = "Сессии опросов"
        ordering = ["-started_at"]
        unique_together = ["user", "category", "attempt"]

    def __str__(self):
        return f"{self.user} - {self.category.name} (попытка {self.attempt}) - {self.get_status_display()}"

    @property
    def progress(self):
        """Прогресс прохождения опроса (только для текущей сессии)"""
        total_questions = SurveyQuestion.objects.filter(
            block__category=self.category, is_active=True
        ).count()
        if total_questions == 0:
            return 0
        answered = UserSurveyResponse.objects.filter(
            user=self.user, question__block__category=self.category, session=self
        ).count()
        return round(answered / total_questions * 100)


class UserSurveyResponse(models.Model):
    """Ответ пользователя на опрос"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="survey_responses",
        verbose_name="Пользователь",
    )
    session = models.ForeignKey(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Сессия",
        null=True,
        blank=True,
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name="Вопрос",
    )
    score = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        verbose_name="Оценка",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата ответа")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"
        unique_together = ["user", "question", "session"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.question.text[:30]} - {self.score}"


class SurveyInterpretation(models.Model):
    """Интерпретация результатов опроса (рекомендации, описания уровней)"""

    SURVEY_TYPES = [
        ("digcomp", "DigCompEdu"),
        ("riasec", "RIASEC"),
        ("big5", "Big5 (Большая пятёрка)"),
        ("gardner", "Gardner (Множественный интеллект)"),
        ("custom", "Пользовательский"),
    ]

    USER_TYPES = [
        ("employee", "Работник"),
        ("employer", "Работодатель"),
        ("university", "ВУЗ"),
        ("common", "Общий"),
    ]

    survey_type = models.CharField(
        max_length=20, choices=SURVEY_TYPES, verbose_name="Тип опроса"
    )
    code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Код/Уровень"
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default="common",
        verbose_name="Тип пользователя",
    )

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание/Характеристика"
    )
    recommendations = models.TextField(
        blank=True, null=True, verbose_name="Рекомендации"
    )
    fields_list = models.TextField(
        blank=True, null=True, verbose_name="Подходящие сферы"
    )

    # Для интерпретации черт (Big5)
    high_description = models.TextField(
        blank=True, null=True, verbose_name="Описание высокого уровня"
    )
    low_description = models.TextField(
        blank=True, null=True, verbose_name="Описание низкого уровня"
    )

    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # Важные замечания (общие для всего опроса)
    important_notes = models.TextField(
        blank=True, null=True, verbose_name="Важные замечания"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Интерпретация опроса"
        verbose_name_plural = "Интерпретации опросов"
        ordering = ["survey_type", "order", "code"]
        unique_together = ["survey_type", "code", "user_type"]

    def __str__(self):
        return f"{self.get_survey_type_display()} - {self.code or 'common'} - {self.get_user_type_display()}"


class DigCompResult(models.Model):
    """Результаты DigCompEdu теста"""

    session = models.OneToOneField(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="digcomp_result",
        verbose_name="Сессия опроса",
    )

    # Баллы по областям (максимум 50 каждая)
    area1_score = models.PositiveSmallIntegerField(verbose_name="Область 1 балл")
    area2_score = models.PositiveSmallIntegerField(verbose_name="Область 2 балл")
    area3_score = models.PositiveSmallIntegerField(verbose_name="Область 3 балл")
    area4_score = models.PositiveSmallIntegerField(verbose_name="Область 4 балл")
    area5_score = models.PositiveSmallIntegerField(verbose_name="Область 5 балл")

    # total_score = models.PositiveSmallIntegerField(verbose_name="Общий балл")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Результат DigCompEdu"
        verbose_name_plural = "Результаты DigCompEdu"

    def __str__(self):
        return f"{self.session.user}"


class RiasacResult(models.Model):
    """Результаты опросника RIASEC (Холланд)"""

    session = models.OneToOneField(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="riasac_result",
        verbose_name="Сессия опроса",
    )

    # Баллы по типам (максимум 50 каждый - 10 вопросов * 5 баллов)
    r_score = models.PositiveSmallIntegerField(verbose_name="Реалистичный (R) балл")
    i_score = models.PositiveSmallIntegerField(
        verbose_name="Исследовательский (I) балл"
    )
    a_score = models.PositiveSmallIntegerField(verbose_name="Артистический (A) балл")
    s_score = models.PositiveSmallIntegerField(verbose_name="Социальный (S) балл")
    e_score = models.PositiveSmallIntegerField(
        verbose_name="Предпринимательский (E) балл"
    )
    c_score = models.PositiveSmallIntegerField(verbose_name="Конвенциональный (C) балл")

    # Карьерный код (3 буквы в порядке убывания)
    career_code = models.CharField(max_length=3, verbose_name="Карьерный код")

    # Доминирующие типы (для хранения)
    dominant_types = models.CharField(max_length=50, verbose_name="Доминирующие типы")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Результат RIASEC"
        verbose_name_plural = "Результаты RIASEC"

    def __str__(self):
        return f"{self.session.user} - {self.career_code}"

    def get_scores_dict(self):
        """Словарь баллов по типам"""
        return {
            "R": self.r_score,
            "I": self.i_score,
            "A": self.a_score,
            "S": self.s_score,
            "E": self.e_score,
            "C": self.c_score,
        }

    def get_level_for_score(self, score):
        """Определяет уровень выраженности по баллу"""
        if 10 <= score <= 20:
            return "low"
        elif 21 <= score <= 35:
            return "medium"
        elif 36 <= score <= 50:
            return "high"
        return "low"


class Big5Result(models.Model):
    """Результаты опросника Большая пятёрка (Big5)"""

    session = models.OneToOneField(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="big5_result",
        verbose_name="Сессия опроса",
    )

    extraversion_score = models.PositiveSmallIntegerField(verbose_name="Экстраверсия")
    agreeableness_score = models.PositiveSmallIntegerField(
        verbose_name="Доброжелательность"
    )
    conscientiousness_score = models.PositiveSmallIntegerField(
        verbose_name="Добросовестность"
    )
    neuroticism_score = models.PositiveSmallIntegerField(verbose_name="Нейротизм")
    openness_score = models.PositiveSmallIntegerField(verbose_name="Открытость опыту")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Результат Big5"
        verbose_name_plural = "Результаты Big5"

    def __str__(self):
        return f"{self.session.user} - Big5"


class GardnerResult(models.Model):
    """Результаты опросника множественного интеллекта (Гарднер)"""

    session = models.OneToOneField(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="gardner_result",
        verbose_name="Сессия опроса",
    )

    linguistic_score = models.PositiveSmallIntegerField(verbose_name="Лингвистический")
    logical_score = models.PositiveSmallIntegerField(
        verbose_name="Логико-математический"
    )
    spatial_score = models.PositiveSmallIntegerField(verbose_name="Пространственный")
    musical_score = models.PositiveSmallIntegerField(verbose_name="Музыкальный")
    kinesthetic_score = models.PositiveSmallIntegerField(
        verbose_name="Телесно-кинестетический"
    )
    interpersonal_score = models.PositiveSmallIntegerField(verbose_name="Межличностный")
    intrapersonal_score = models.PositiveSmallIntegerField(
        verbose_name="Внутриличностный"
    )
    naturalistic_score = models.PositiveSmallIntegerField(
        verbose_name="Натуралистический"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Результат Гарднера"
        verbose_name_plural = "Результаты Гарднера"

    def __str__(self):
        return f"{self.session.user} - Gardner"
