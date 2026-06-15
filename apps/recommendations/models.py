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
