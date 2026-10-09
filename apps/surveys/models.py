from django.db import models
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags
import re

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
    # ========== Ограничения аудитории ==========
    target_user_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Типы пользователей",
        help_text="Список user_type, которым доступен опрос. " "Пусто — доступен всем.",
    )
    target_organization_type = models.ForeignKey(
        "organizations.OrganizationType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="survey_categories",
        verbose_name="Тип организации",
        help_text="Если указан — опрос видят только работники организаций этого типа.",
    )
    target_positions = models.ManyToManyField(
        "accounts.Position",
        blank=True,
        related_name="survey_categories",
        verbose_name="Должности",
        help_text="Если указаны — опрос видят только работники с этими должностями.",
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
            block__category=self,
            block__is_active=True,
            is_active=True,
        ).count()

    def get_display_description(self):
        """Получить описание для отображения (без технической информации)"""
        if self.description and "Импортирован из Excel" in self.description:
            return "Пройдите опрос, чтобы оценить свои навыки"
        return self.description or "Пройдите опрос, чтобы оценить свои навыки"

    def get_result_description_clean(self):
        """
        Возвращает чистый текст из result_description без HTML-тегов.
        Используется для передачи в AI.
        """
        if not self.result_description:
            return None

        # Удаляем HTML-теги
        text = strip_tags(self.result_description)
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r"\s+", " ", text).strip()
        # Обрезаем до 1500 символов
        if len(text) > 1500:
            text = text[:1500] + "..."
        return text

    def is_available_for(self, user):
        """Проверяет, доступен ли опрос данному пользователю."""
        # 1. Тип пользователя
        if self.target_user_types:
            if user.user_type not in self.target_user_types:
                return False

        # 2. Тип организации
        if self.target_organization_type_id:
            profile = getattr(user, "employee_profile", None)
            if not profile or not profile.organization:
                return False
            if (
                profile.organization.organization_type_id
                != self.target_organization_type_id
            ):
                return False

        # 3. Должности
        position_ids = list(self.target_positions.values_list("id", flat=True))
        if position_ids:
            profile = getattr(user, "employee_profile", None)
            if not profile:
                return False
            # Сопоставляем по названию должности (у EmployeeProfile.position — CharField)
            profile_position_name = (profile.position or "").strip()
            allowed_names = set(self.target_positions.values_list("name", flat=True))
            if profile_position_name not in allowed_names:
                return False

        return True


class SurveyBlock(models.Model):
    """Блок вопросов (раздел опроса)"""

    category = models.ForeignKey(
        SurveyCategory,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Категория опроса",
    )
    title = models.CharField(max_length=255, verbose_name="Название блока")
    subtitle = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Подзаголовок / расшифровка",
    )
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

    # Группа варианта (А/Б/В/Г) — только для опросов с опциями
    # (например, диагностический комплект руководителя ОО).
    # Для обычных опросов со шкалой 1–5 остаётся NULL.
    group = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        verbose_name="Группа (А/Б/В/Г)",
    )

    # Оценка по шкале 1–5 (для опросов DigComp, RIASEC, Big5, Gardner).
    # Для опросов с опциями может быть NULL — там важен selected_option.
    score = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")],
        verbose_name="Оценка",
        null=True,
        blank=True,
    )

    # Выбранный вариант для опросов с опциями.
    selected_option = models.ForeignKey(
        "SurveyQuestionOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responses",
        verbose_name="Выбранный вариант",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата ответа")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"
        # Уникальность на уровне (пользователь, вопрос, сессия, группа).
        # Для опросов со шкалой 1–5 group = NULL, поэтому одна запись
        # на (user, question, session) сохраняется.
        # Для опросов с опциями на один вопрос приходится 4 записи —
        # по одной на каждую группу А/Б/В/Г.
        unique_together = ("user", "question", "session", "group")
        ordering = ["-created_at"]

    def __str__(self):
        if self.group:
            return f"{self.user} - {self.question.text[:30]} - {self.group}"
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


class RiasecCodeInterpretation(models.Model):
    """Интерпретация трёхбуквенного кода RIASEC (120 комбинаций)"""

    RIASEC_LETTERS = [
        ("R", "Реалистичный"),
        ("I", "Исследовательский"),
        ("A", "Артистический"),
        ("S", "Социальный"),
        ("E", "Предприимчивый"),
        ("C", "Конвенциональный"),
    ]

    code = models.CharField(
        max_length=3,
        unique=True,
        db_index=True,
        verbose_name="Трёхбуквенный код",
        help_text="Например: RIA, SEC, AIC",
    )

    dominant = models.CharField(
        max_length=1,
        choices=RIASEC_LETTERS,
        verbose_name="Доминирующий тип",
        db_index=True,
    )
    secondary = models.CharField(
        max_length=1,
        choices=RIASEC_LETTERS,
        verbose_name="Дополнительный тип",
    )
    tertiary = models.CharField(
        max_length=1,
        choices=RIASEC_LETTERS,
        verbose_name="Поддерживающий тип",
    )

    description = models.TextField(
        verbose_name="Описание склонностей",
        help_text="Например: «склонность к практической, технической работе...»",
    )
    professions = models.TextField(
        verbose_name="Подходящие профессии",
        help_text="Через запятую или по одной на строку",
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Интерпретация кода RIASEC"
        verbose_name_plural = "Интерпретации кодов RIASEC"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["dominant"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.description[:60]}"

    def get_professions_list(self):
        """Возвращает список профессий"""
        if not self.professions:
            return []
        # поддерживаем и запятые, и переводы строк
        text = self.professions.replace("\n", ",")
        return [p.strip() for p in text.split(",") if p.strip()]


class ProfessionalStandard(models.Model):
    """Профстандарт"""

    EDUCATION_LEVELS = [
        ("VO", "Высшее образование"),
        ("SPO", "Среднее профессиональное образование"),
    ]

    code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Код ПС",
        help_text="Например: 10.028",
    )
    name = models.TextField(
        verbose_name="Наименование ПС",
    )
    education_level = models.CharField(
        max_length=5,
        choices=EDUCATION_LEVELS,
        verbose_name="Уровень образования",
        db_index=True,
    )

    riasec_codes = models.ManyToManyField(
        "RiasecCodeInterpretation",
        related_name="professional_standards",
        blank=True,
        verbose_name="Коды Холланда",
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профстандарт"
        verbose_name_plural = "Профстандарты"
        ordering = ["education_level", "code"]
        unique_together = ["code", "education_level"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["education_level"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name[:80]}"


class GeneralizedLaborFunction(models.Model):
    """
    Обобщённая трудовая функция (ОТФ) внутри профстандарта.
    """

    professional_standard = models.ForeignKey(
        ProfessionalStandard,
        on_delete=models.CASCADE,
        related_name="labor_functions",
        verbose_name="Профстандарт",
    )
    code = models.CharField(
        max_length=50,
        verbose_name="Код ОТФ",
        help_text="Например: A, B, C или A/01.6",
    )
    name = models.TextField(
        verbose_name="Наименование ОТФ",
    )
    qualification_level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Уровень квалификации",
        help_text="1-9, если указан",
    )
    order = models.PositiveSmallIntegerField(default=1, verbose_name="Порядок")

    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Обобщённая трудовая функция"
        verbose_name_plural = "Обобщённые трудовые функции"
        ordering = ["professional_standard", "order", "code"]
        unique_together = ["professional_standard", "code"]

    def __str__(self):
        return f"{self.professional_standard.code} - {self.code}. {self.name[:60]}"


class EducationProgram(models.Model):
    """ФГОС ВО или ФГОС СПО (направление подготовки / специальность)"""

    education_level = models.CharField(
        max_length=5,
        choices=ProfessionalStandard.EDUCATION_LEVELS,
        verbose_name="Уровень образования",
        db_index=True,
    )
    code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Код ФГОС",
        help_text="Например: 07.03.03, 39.03.02",
    )
    name = models.TextField(
        verbose_name="Наименование ФГОС",
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ФГОС (направление, специальность)"
        verbose_name_plural = "ФГОС (направления, специальности)"
        ordering = ["education_level", "code"]
        unique_together = ["code", "name", "education_level"]

    def __str__(self):
        return f"{self.code} - {self.name[:80]}"


class ProfessionalStandardProgram(models.Model):
    """
    Связь профстандарта и ФГОС.
    Дополнительно хранит порядковый номер (1-5) из Excel.
    """

    professional_standard = models.ForeignKey(
        ProfessionalStandard,
        on_delete=models.CASCADE,
        related_name="program_links",
        verbose_name="Профстандарт",
    )
    education_program = models.ForeignKey(
        EducationProgram,
        on_delete=models.CASCADE,
        related_name="standard_links",
        verbose_name="ФГОС",
    )
    order = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Порядок",
        help_text="1-5, как в исходной таблице",
    )

    class Meta:
        verbose_name = "Связь профстандарта и ФГОС"
        verbose_name_plural = "Связи профстандартов и ФГОС"
        ordering = ["professional_standard", "order"]
        unique_together = ["professional_standard", "education_program"]

    def __str__(self):
        return f"{self.professional_standard.code} - {self.education_program.code} (#{self.order})"


class SurveyQuestionOption(models.Model):
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )
    group = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        verbose_name="Группа (А/Б/В/Г)",
    )
    text = models.TextField(verbose_name="Текст варианта")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        ordering = ["question", "order"]

    def __str__(self):
        prefix = f"[{self.group}] " if self.group else ""
        return f"{prefix}{self.question.text[:40]} — {self.text[:40]}"


class DiagnosticKitResult(models.Model):
    session = models.OneToOneField(
        SurveySession,
        on_delete=models.CASCADE,
        related_name="diagnostic_kit_result",
    )
    work1_score = models.PositiveSmallIntegerField(default=0)
    work2_score = models.PositiveSmallIntegerField(default=0)
    work3_score = models.PositiveSmallIntegerField(default=0)
    work4_score = models.PositiveSmallIntegerField(default=0)
    total_score = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Результат диагностического комплекта"
        verbose_name_plural = "Результаты диагностических комплектов"

    def __str__(self):
        return f"{self.session.user} — {self.total_score}/40"

    @staticmethod
    def level_for_work(score):
        if 0 <= score <= 4:
            return {"code": "low", "name": "Низкий уровень", "color": "danger"}
        if 5 <= score <= 6:
            return {"code": "medium", "name": "Средний уровень", "color": "warning"}
        if 7 <= score <= 8:
            return {"code": "high", "name": "Высокий уровень", "color": "info"}
        if 9 <= score <= 10:
            return {"code": "expert", "name": "Экспертный уровень", "color": "success"}
        return {"code": "unknown", "name": "—", "color": "secondary"}

    @staticmethod
    def level_for_total(score):
        if 0 <= score <= 16:
            return {"code": "low", "name": "Низкий уровень", "color": "danger"}
        if 17 <= score <= 26:
            return {"code": "medium", "name": "Средний уровень", "color": "warning"}
        if 27 <= score <= 34:
            return {"code": "high", "name": "Высокий уровень", "color": "info"}
        if 35 <= score <= 40:
            return {"code": "expert", "name": "Экспертный уровень", "color": "success"}
        return {"code": "unknown", "name": "—", "color": "secondary"}

    def get_works_data(self):
        scores = [
            self.work1_score,
            self.work2_score,
            self.work3_score,
            self.work4_score,
        ]
        result = []
        for i, s in enumerate(scores, start=1):
            # Найти блок с названием «Диагностическая работа i»
            block = SurveyBlock.objects.filter(
                category=self.session.category,
                title__icontains=f"работа {i}",
            ).first()

            name = (
                block.subtitle
                if block and block.subtitle
                else (block.title if block else f"Работа {i}")
            )

            result.append(
                {
                    "num": i,
                    "name": name,
                    "score": s,
                    "percent": round(s / 10 * 100),
                    "level": self.level_for_work(s),
                }
            )
        return result
