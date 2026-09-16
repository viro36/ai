import uuid
from django.conf import settings
from django.db import models


class ExportJob(models.Model):
    """История выгрузок"""

    STATUS_CHOICES = [
        ("pending", "В обработке"),
        ("done", "Готово"),
        ("failed", "Ошибка"),
    ]

    EXPORT_TYPES = [
        ("employees_full", "Работники: профили + RIASEC + рекомендации + курсы"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export_type = models.CharField(max_length=50, choices=EXPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_jobs",
    )
    file = models.FileField(upload_to="exports/%Y/%m/%d/", null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    filters = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Выгрузка"
        verbose_name_plural = "Выгрузки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_export_type_display()} — {self.get_status_display()} ({self.created_at:%Y-%m-%d %H:%M})"
