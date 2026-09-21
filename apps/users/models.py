from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.organizations.models import Organization


class CustomUser(AbstractUser):
    """Расширенная модель пользователя"""

    # Типы пользователей
    class UserType(models.TextChoices):
        REGULAR = "regular", "Обычный пользователь"
        # ESIA = "esia", "Пользователь ЕСИА"
        # TEACHER = "teacher", "Преподаватель"
        EMPLOYER = "employer", "Работодатель"
        EMPLOYEE = "employee", "Работник"
        UNIVERSITY = "university", "ВУЗ"
        ADMIN = "admin", "Администратор"
        MINTUD = "mintrud", "Минтруд"

    # Основные поля
    snils = models.CharField(
        max_length=14, unique=True, null=True, blank=True, verbose_name="СНИЛС"
    )
    patronymic = models.CharField(max_length=150, blank=True, verbose_name="Отчество")
    birthday = models.DateField(null=True, blank=True, verbose_name="Дата рождения")

    # Флаги и типы
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.REGULAR,
        verbose_name="Тип пользователя",
    )

    # Связь с организацией
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Организация",
    )

    # ESIA связь
    esia_id = models.CharField(
        max_length=50, unique=True, null=True, blank=True, verbose_name="ID в ЕСИА"
    )
    esia_verified = models.BooleanField(
        default=False, verbose_name="Подтвержден через ЕСИА"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        indexes = [
            models.Index(fields=["user_type"]),
            models.Index(fields=["esia_id"]),
        ]

    def __str__(self):
        # Возвращаем имя пользователя или полное имя
        if self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name}"
        return self.username

    @property
    def full_name(self):
        """Полное имя с отчеством"""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)

    @property
    def is_esia_user(self):
        """Проверка, зарегистрирован ли пользователь через ЕСИА"""
        return self.user_type == self.UserType.ESIA or bool(self.esia_id)
