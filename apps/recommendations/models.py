from django.db import models
from django.conf import settings


class CourseRecommendation(models.Model):
    """Рекомендации курсов для пользователя"""

    STATUS_CHOICES = [
        ("pending", "В обработке"),
        ("completed", "Завершено"),
        ("failed", "Ошибка"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_recommendations",
        verbose_name="Пользователь",
    )
    session = models.ForeignKey(
        "surveys.SurveySession",
        on_delete=models.CASCADE,
        related_name="recommendations",
        verbose_name="Сессия опросов",
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="recommendations",
        verbose_name="Рекомендованный курс",
    )
    reason = models.TextField(verbose_name="Причина рекомендации")
    relevance_score = models.FloatField(
        default=0.0, verbose_name="Оценка релевантности (0-1)"
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_viewed = models.BooleanField(default=False, verbose_name="Просмотрено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Рекомендация курса"
        verbose_name_plural = "Рекомендации курсов"
        ordering = ["order", "-relevance_score"]

    def __str__(self):
        return f"{self.user} -> {self.course.title}"

    def get_relevance_percent(self):
        """Возвращает релевантность в процентах (0-100)"""
        return round(self.relevance_score * 100)


class RecommendationTask(models.Model):
    """Статус задачи генерации рекомендаций"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendation_task",
        verbose_name="Пользователь",
    )
    task_id = models.CharField(max_length=255, verbose_name="ID задачи Celery")
    status = models.CharField(
        max_length=20, choices=CourseRecommendation.STATUS_CHOICES, default="pending"
    )
    error_message = models.TextField(blank=True, null=True, verbose_name="Ошибка")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Задача рекомендаций"
        verbose_name_plural = "Задачи рекомендаций"

    def __str__(self):
        return f"{self.user} - {self.status}"


class SelectedCourse(models.Model):
    """Выбранные пользователем курсы"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="selected_courses",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="selected_by_users",
        verbose_name="Курс",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выбора")

    class Meta:
        verbose_name = "Выбранный курс"
        verbose_name_plural = "Выбранные курсы"
        unique_together = ["user", "course"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.course.title}"


class ApprovedSelectedCourse(models.Model):
    """Одобренные/неодобренные выбранные курсы работника работодателем"""

    STATUS_CHOICES = [
        ("pending", "На рассмотрении"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    ]

    selected_course = models.OneToOneField(
        SelectedCourse,
        on_delete=models.CASCADE,
        related_name="approval",
        verbose_name="Выбранный курс",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Статус одобрения",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_courses",
        verbose_name="Кем одобрено",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата одобрения/отклонения",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Одобрение курса"
        verbose_name_plural = "Одобрения курсов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.selected_course.user} -> {self.selected_course.course.title}: {self.get_status_display()}"


class EmployerRecommendation(models.Model):
    """Рекомендации курсов от работодателя работнику"""

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_recommendations",
        verbose_name="Работодатель",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_recommendations",
        verbose_name="Работник",
        limit_choices_to={"user_type": "employee"},
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="employer_recommendations",
        verbose_name="Рекомендованный курс",
    )
    reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Причина рекомендации",
    )
    is_viewed = models.BooleanField(default=False, verbose_name="Просмотрено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Рекомендация от работодателя"
        verbose_name_plural = "Рекомендации от работодателей"
        ordering = ["-created_at"]
        unique_together = ["employer", "employee", "course"]

    def __str__(self):
        return f"{self.employer} -> {self.employee} -> {self.course.title}"
