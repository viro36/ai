from django.db import models
from django.contrib.auth import get_user_model


class District(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="Полное название")
    short_name = models.CharField(max_length=255, verbose_name="Краткое название")

    class Meta:
        verbose_name = "Район"
        verbose_name_plural = "Районы"
        ordering = ["short_name"]

    def __str__(self):
        return self.short_name


class OrganizationType(models.Model):
    """Тип организации"""

    name = models.CharField(max_length=255, verbose_name="Название типа")

    class Meta:
        verbose_name = "Тип организации"
        verbose_name_plural = "Типы организаций"

    def __str__(self):
        return self.name


class Organization(models.Model):
    """
    Данные будут частично заполняться из API DaData по ИНН.
    """

    STATUS_CHOICES = [
        ("ACTIVE", "Действующая"),
        ("LIQUIDATING", "Ликвидируется"),
        ("LIQUIDATED", "Ликвидирована"),
        (
            "REORGANIZING",
            "В процессе присоединения к другому юрлицу, с последующей ликвидацией",
        ),
        ("BANKRUPT", "Банкротство"),
    ]

    BRANCH_TYPE_CHOICES = [
        ("MAIN", "Головная организация"),
        ("BRANCH", "Филиал"),
    ]

    ORG_TYPE_CHOICES = [
        ("LEGAL", "Юридическое лицо"),
        ("INDIVIDUAL", "Индивидуальный предприниматель"),
    ]

    # ========== Основные реквизиты ==========
    inn = models.CharField(
        max_length=12, unique=True, db_index=True, verbose_name="ИНН"
    )
    kpp = models.CharField(max_length=20, blank=True, null=True, verbose_name="КПП")
    kpp_largest = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="КПП крупнейшего налогоплательщика",
    )
    ogrn = models.CharField(max_length=20, blank=True, null=True, verbose_name="ОГРН")
    ogrn_date = models.DateField(blank=True, null=True, verbose_name="Дата выдачи ОГРН")
    hid = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="HID DaData"
    )
    org_type = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Тип организации"
    )

    # ========== Наименования ==========
    full_name = models.TextField(verbose_name="Полное наименование")
    short_name = models.CharField(max_length=500, verbose_name="Краткое наименование")
    full_name_without_opf = models.TextField(
        blank=True, null=True, verbose_name="Полное наименование без ОПФ"
    )
    short_name_without_opf = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Краткое наименование без ОПФ",
    )
    latin_name = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Наименование на латинице"
    )

    # ========== ФИО для ИП ==========
    fio_surname = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Фамилия ИП"
    )
    fio_name = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Имя ИП"
    )
    fio_patronymic = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Отчество ИП"
    )

    # ========== ОПФ ==========
    opf_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Код ОКОПФ"
    )
    opf_full = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="Полное название ОПФ"
    )
    opf_short = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Краткое название ОПФ"
    )
    opf_type = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Версия ОКОПФ"
    )

    # ========== Адрес ==========
    address_raw = models.TextField(verbose_name="Адрес (строка)")
    address_source = models.TextField(
        blank=True, null=True, verbose_name="Адрес из ЕГРЮЛ"
    )
    address_qc = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Код проверки адреса"
    )
    postal_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Индекс"
    )
    region = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="Регион"
    )
    city = models.CharField(max_length=300, blank=True, null=True, verbose_name="Город")
    street = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Улица"
    )
    house = models.CharField(max_length=100, blank=True, null=True, verbose_name="Дом")

    # ========== Координаты ==========
    coordinates = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Координаты"
    )

    # ========== Статус и состояние ==========
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Статус",
    )
    status_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Детальный код статуса"
    )
    actuality_date = models.DateField(
        blank=True, null=True, verbose_name="Дата актуальности"
    )
    registration_date = models.DateField(
        blank=True, null=True, verbose_name="Дата регистрации"
    )
    liquidation_date = models.DateField(
        blank=True, null=True, verbose_name="Дата ликвидации"
    )

    # ========== Коды статистики ==========
    okpo = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКПО")
    okato = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКАТО")
    oktmo = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКТМО")
    okogu = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКОГУ")
    okfs = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКФС")
    okved = models.CharField(max_length=50, blank=True, null=True, verbose_name="ОКВЭД")
    okved_type = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Версия ОКВЭД"
    )

    # ========== Руководство ==========
    manager_name = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Руководитель"
    )
    manager_post = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="Должность руководителя"
    )
    manager_start_date = models.DateField(
        blank=True, null=True, verbose_name="Дата вступления в должность"
    )

    # ========== Филиалы ==========
    branch_count = models.IntegerField(
        blank=True, null=True, verbose_name="Количество филиалов"
    )
    branch_type = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Тип подразделения"
    )

    # ========== Связи ==========
    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Тип организации",
    )
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Район"
    )

    # ========== Временные метки ==========
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"
        indexes = [
            models.Index(fields=["inn"]),
            models.Index(fields=["short_name"]),
            models.Index(fields=["district"]),
            models.Index(fields=["organization_type"]),
        ]

    def __str__(self):
        return f"{self.short_name} (ИНН: {self.inn})"

    @property
    def courses_count(self):
        """Общее количество курсов"""
        return self.courses.count()

    @property
    def active_courses_count(self):
        """Количество активных курсов"""
        return self.courses.filter(is_deleted=False).count()

    @property
    def deleted_courses_count(self):
        """Количество удалённых курсов"""
        return self.courses.filter(is_deleted=True).count()

    @property
    def employee_count(self):
        """Количество сотрудников в организации"""
        User = get_user_model()
        return User.objects.filter(
            organization=self, user_type="employee", is_active=True
        ).count()

    @property
    def selected_courses_count(self):
        """Количество одобренных курсов организации, выбранных работниками"""
        from apps.recommendations.models import SelectedCourse

        return (
            SelectedCourse.objects.filter(
                course__organization=self,
                course__is_deleted=False,
                approval__status="approved",
            )
            .values("course")
            .distinct()
            .count()
        )

    @property
    def received_requirements_count(self):
        """Количество полученных ТЗ со статусом 'Отправлено'"""
        from apps.technical_requirements.models import (
            TechnicalRequirementUniversity,
            RequirementStatus,
        )

        try:
            sent_status = RequirementStatus.objects.get(code=1)
            return TechnicalRequirementUniversity.objects.filter(
                university=self, status=sent_status
            ).count()
        except RequirementStatus.DoesNotExist:
            return 0
