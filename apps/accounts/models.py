from django.db import models
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization

User = get_user_model()


class EmployerRegistrationRequest(models.Model):
    """Заявка на регистрацию работодателя"""

    STATUS_CHOICES = [
        ("pending", "На рассмотрении"),
        ("approved", "Одобрено"),
        ("rejected", "Отклонено"),
    ]

    # Стандартные поля пользователя
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    password = models.CharField(max_length=128)  # будет хранить хеш пароля

    # Поля работодателя
    short_name = models.CharField(
        max_length=255, verbose_name="Краткое название организации"
    )
    full_name = models.TextField(verbose_name="Полное название организации")
    inn = models.CharField(max_length=12, verbose_name="ИНН")

    # Статус заявки
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Связь с созданным пользователем и организацией после одобрения
    created_user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employer_request",
    )
    created_organization = models.OneToOneField(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employer_request",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Заявка на регистрацию работодателя"
        verbose_name_plural = "Заявки на регистрацию работодателей"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_name} ({self.get_status_display()})"


class EmployerProfile(models.Model):
    """Профиль организации (Работодатель / ВУЗ)"""

    user = models.OneToOneField(
        "users.CustomUser", on_delete=models.CASCADE, related_name="employer_profile"
    )

    # ========== 1. Контактная информация ==========
    actual_address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Фактический адрес (если отличается от юридического)",
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Телефон организации"
    )
    email = models.EmailField(
        blank=True, null=True, verbose_name="Адрес электронной почты организации"
    )
    website = models.URLField(blank=True, null=True, verbose_name="Сайт организации")

    # Контактное лицо
    contact_person_full_name = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="ФИО контактного лица"
    )
    contact_person_position = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Должность контактного лица"
    )
    contact_person_phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Телефон контактного лица"
    )
    contact_person_email = models.EmailField(
        blank=True, null=True, verbose_name="Email контактного лица"
    )

    # ========== 2. Реквизиты ==========
    checking_account = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Расчётный счёт"
    )
    bank_name = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="Банк"
    )
    bik = models.CharField(max_length=9, blank=True, null=True, verbose_name="БИК")
    correspondent_account = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Корреспондентский счёт"
    )

    # ========== 3. Основные показатели деятельности ==========
    employee_count = models.IntegerField(
        blank=True, null=True, verbose_name="Текущая численность сотрудников (человек)"
    )
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Объём производства/выручки за прошлый календарный год (в рублях)",
    )

    # ========== Специальные поля для ВУЗов ==========
    license_link = models.URLField(
        blank=True, null=True, verbose_name="Ссылка на лицензию (Рособрнадзор)"
    )
    dpo_programs_link = models.URLField(
        blank=True, null=True, verbose_name="Ссылка на перечень программ ДПО"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профиль работодателя"
        verbose_name_plural = "Профили работодателей"

    def __str__(self):
        return f"Профиль {self.user.organization.short_name if self.user.organization else self.user.username}"


# --------------------------------------------------------------------------------------


class EmployeeProfile(models.Model):
    """Профиль работника (создаётся сразу при регистрации)"""

    POSITION_LEVEL_CHOICES = [
        ("top", "Руководитель высшего звена"),
        ("middle", "Руководитель среднего звена"),
        ("lower", "Руководитель низового звена"),
        ("specialist", "Специалист"),
        ("office", "Служащий"),
        ("worker", "Рабочий"),
    ]

    GENDER_CHOICES = [
        ("M", "Мужской"),
        ("F", "Женский"),
    ]

    EMPLOYMENT_STATUS_CHOICES = [
        ("employed", "Работаю по найму"),
        ("self_employed", "Самозанятый"),
        ("entrepreneur", "ИП"),
        ("unemployed", "Безработный"),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ("secondary", "Среднее"),
        ("secondary_special", "Среднее специальное"),
        ("higher", "Высшее"),
        ("academic_degree", "Ученая степень"),
    ]

    user = models.OneToOneField(
        "users.CustomUser", on_delete=models.CASCADE, related_name="employee_profile"
    )

    # ========== Существующие поля ==========
    snils = models.CharField(max_length=14, unique=True, verbose_name="СНИЛС")
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        verbose_name="Организация",
    )
    position = models.CharField(max_length=255, verbose_name="Должность")
    position_level = models.CharField(
        max_length=20,
        choices=POSITION_LEVEL_CHOICES,
        verbose_name="Категория должности",
    )

    # ========== НОВЫЕ ПОЛЯ ==========

    # 1. Персональные данные
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, verbose_name="Пол", blank=True, null=True
    )
    citizenship = models.CharField(
        max_length=100,
        default="Россия",
        verbose_name="Гражданство",
        blank=True,
        null=True,
    )

    # 2. Контактные данные
    phone = models.CharField(
        max_length=20, verbose_name="Номер телефона", blank=True, null=True
    )
    municipality = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Муниципалитет"
    )
    locality = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="Населенный пункт"
    )

    # 3. Информация о трудоустройстве
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        verbose_name="Статус занятости",
        blank=True,
        null=True,
    )
    work_experience_years = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Стаж работы (лет)"
    )

    # 4. Образование
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name="Уровень образования",
        blank=True,
        null=True,
    )
    education_institution = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Название учебного заведения",
    )
    graduation_year = models.IntegerField(
        blank=True, null=True, verbose_name="Год окончания"
    )
    specialty = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Специальность/направление подготовки",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профиль работника"
        verbose_name_plural = "Профили работников"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.organization.short_name}"
