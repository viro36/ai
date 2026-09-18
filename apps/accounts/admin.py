from django import forms
from django.urls import path
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter

from django.utils.safestring import mark_safe
from django.urls import reverse

from apps.organizations.models import Organization
from apps.users.models import CustomUser
from .models import EmployerProfile, EmployerRegistrationRequest, EmployeeProfile
from .admin_views import (
    approve_employer_request,
    reject_employer_request,
    process_approve,
    employee_full_profile,
)


# ============================================================
# Заявки на регистрацию работодателей
# ============================================================
@admin.register(EmployerRegistrationRequest)
class EmployerRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_name",
        "inn",
        "username",
        "email",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("short_name", "full_name", "inn", "username", "email")
    readonly_fields = ("created_at", "updated_at")
    actions = ["approve_selected", "reject_selected"]

    def _is_viewer(self, request):
        """Проверка, является ли пользователь просмотрщиком"""
        return request.user.groups.filter(name="Просмотрщик").exists()

    def get_actions(self, request):
        """Скрываем выпадающий список действий для просмотрщика"""
        if self._is_viewer(request):
            return {}  # Возвращаем пустой словарь - действий нет
        return super().get_actions(request)

    def has_add_permission(self, request):
        if self._is_viewer(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_delete_permission(request, obj)

    def approve_selected(self, request, queryset):
        """Массовое одобрение заявок"""
        pending = queryset.filter(status="pending")
        approved_count = 0
        error_count = 0
        existing_org_count = 0

        for registration in pending:
            try:
                org_exists = Organization.objects.filter(inn=registration.inn).exists()
                if org_exists:
                    existing_org_count += 1

                process_approve(registration)
                approved_count += 1
            except Exception as e:
                error_count += 1

        if approved_count:
            msg = f"Одобрено {approved_count} заявок."
            if existing_org_count:
                msg += f" Из них {existing_org_count} привязаны к существующим организациям."
            self.message_user(request, msg)
        if error_count:
            self.message_user(
                request, f"Ошибок при одобрении: {error_count}", messages.ERROR
            )

    approve_selected.short_description = "Одобрить выбранные заявки"

    def reject_selected(self, request, queryset):
        """Массовое отклонение заявок"""
        count = queryset.filter(status="pending").update(status="rejected")
        if count:
            self.message_user(request, f"Отклонено {count} заявок.", messages.WARNING)
        else:
            self.message_user(request, "Нет заявок на рассмотрении.", messages.INFO)

    reject_selected.short_description = "Отклонить выбранные заявки"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "approve/<int:request_id>/",
                approve_employer_request,
                name="approve_employer_request",
            ),
            path(
                "reject/<int:request_id>/",
                reject_employer_request,
                name="reject_employer_request",
            ),
        ]
        return custom_urls + urls


# ============================================================
# Профиль работодателя / ВУЗа
# ============================================================
class EmployerProfileForm(forms.ModelForm):
    """Форма для профиля организации с ограничением выбора пользователей"""

    class Meta:
        model = EmployerProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        queryset = CustomUser.objects.filter(user_type__in=["employer", "university"])
        self.fields["user"].queryset = queryset

        # Принудительно устанавливаем начальное значение при редактировании
        if self.instance and self.instance.pk:
            self.fields["user"].initial = self.instance.user_id


class UserTypeFilter(SimpleListFilter):
    """Фильтр по типу пользователя"""

    title = "Тип организации"
    parameter_name = "user_type"

    def lookups(self, request, model_admin):
        return (
            ("employer", "Работодатель"),
            ("university", "ВУЗ"),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__user_type=self.value())
        return queryset


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """Админка для профилей организаций (работодателей и ВУЗов)"""

    form = EmployerProfileForm

    list_display = (
        "id",
        "user_link",
        "org_name",
        "org_type_display",
        "phone",
        "email",
        "contact_person",
        "created_at",
    )
    list_filter = (UserTypeFilter, "created_at", "updated_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__organization__short_name",
        "user__organization__inn",
        "phone",
        "email",
        "contact_person_full_name",
    )
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Пользователь",
            {
                "fields": ("user",),
                "description": "Выберите пользователя-работодателя или ВУЗ",
            },
        ),
        (
            "Контактная информация",
            {
                "fields": (
                    "actual_address",
                    ("phone", "email", "website"),
                ),
            },
        ),
        (
            "Контактное лицо",
            {
                "fields": (
                    ("contact_person_full_name", "contact_person_position"),
                    ("contact_person_phone", "contact_person_email"),
                ),
            },
        ),
        (
            "Банковские реквизиты",
            {
                "fields": (
                    ("checking_account", "bank_name"),
                    ("bik", "correspondent_account"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Основные показатели",
            {
                "fields": (("employee_count", "annual_revenue"),),
                "classes": ("collapse",),
            },
        ),
        (
            "Для ВУЗов",
            {
                "fields": (
                    "license_link",
                    "dpo_programs_link",
                ),
                "classes": ("collapse",),
                "description": "Ссылки на лицензию и перечень программ ДПО",
            },
        ),
        (
            "Даты",
            {
                "fields": (("created_at", "updated_at"),),
                "classes": ("collapse",),
            },
        ),
    )

    def _is_viewer(self, request):
        """Проверка, является ли пользователь просмотрщиком"""
        return request.user.groups.filter(name="Просмотрщик").exists()

    def get_actions(self, request):
        """Скрываем выпадающий список действий для просмотрщика"""
        if self._is_viewer(request):
            return {}  # Возвращаем пустой словарь - действий нет
        return super().get_actions(request)

    def has_add_permission(self, request):
        if self._is_viewer(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_delete_permission(request, obj)

    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse("admin:users_customuser_change", args=[obj.user.id])
        return mark_safe(f'<a href="{url}">{obj.user.username}</a>')

    user_link.short_description = "Пользователь"
    user_link.admin_order_field = "user__username"

    def org_name(self, obj):
        """Название организации (только для отображения в списке)"""
        if obj.user.organization:
            return mark_safe(
                f'<a href="/admin/organizations/organization/{obj.user.organization.id}/change/">{obj.user.organization.short_name}</a>'
            )
        return "-"

    org_name.short_description = "Организация"
    org_name.admin_order_field = "user__organization__short_name"

    def org_type_display(self, obj):
        """Тип организации (работодатель/ВУЗ)"""
        if obj.user.user_type == "university":
            return mark_safe(
                '<span style="color: #6f42c1; font-weight: bold;">ВУЗ</span>'
            )
        elif obj.user.user_type == "employer":
            return mark_safe(
                '<span style="color: #28a745; font-weight: bold;">Работодатель</span>'
            )
        return "-"

    org_type_display.short_description = "Тип"
    org_type_display.admin_order_field = "user__user_type"

    def contact_person(self, obj):
        """Контактное лицо"""
        if obj.contact_person_full_name:
            return f"{obj.contact_person_full_name} ({obj.contact_person_phone or '-'})"
        return "-"

    contact_person.short_description = "Контактное лицо"


# ------------------------------------------------------------------------------------------------------


class EmployeeProfileForm(forms.ModelForm):
    """Форма для профиля работника с ограничением выбора пользователей"""

    class Meta:
        model = EmployeeProfile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор пользователей только работниками
        self.fields["user"].queryset = CustomUser.objects.filter(user_type="employee")


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    """Админка для профилей работников"""

    form = EmployeeProfileForm

    list_display = (
        "id",
        "user_link",
        "organization_link",
        "position_level_display",
        "is_unemployed",
        "employment_status",
        "education_level",
        "profile_complete_badge",  # статус анкеты
        "full_profile_link",  # кнопка «Полный профиль»
        "created_at",
    )
    list_filter = (
        "position_level",
        "organization",
        "is_unemployed",
        "employment_status",
        "education_level",
        "created_at",
    )
    search_fields = (
        "user__last_name",
        "user__first_name",
        "user__patronymic",
        "user__snils",
        "organization__short_name",
        "organization__inn",
        "specialty",
    )
    readonly_fields = ("created_at", "updated_at")

    # Шаблон с кнопкой «Полный профиль» на странице редактирования
    change_form_template = "admin/accounts/employeeprofile/change_form.html"

    fieldsets = (
        (
            "Пользователь",
            {
                "fields": ("user",),
            },
        ),
        (
            "Организация и должность",
            {
                "fields": ("organization", "position", "position_level"),
            },
        ),
        (
            "Трудоустройство",
            {
                "fields": (
                    "employment_status",
                    "work_experience_years",
                    "is_unemployed",
                    "is_svo_participant",
                ),
            },
        ),
        (
            "Образование",
            {
                "fields": (
                    "education_level",
                    "education_institution",
                    "graduation_year",
                    "specialty",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Место проживания",
            {
                "fields": ("citizenship", "gender", "municipality", "locality"),
                "classes": ("collapse",),
            },
        ),
        (
            "Даты",
            {
                "fields": (("created_at", "updated_at"),),
                "classes": ("collapse",),
            },
        ),
    )

    # ---------- URL для «Полный профиль» ----------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:profile_id>/full-profile/",
                self.admin_site.admin_view(employee_full_profile),
                name="accounts_employeeprofile_full_profile",
            ),
        ]
        return custom + urls

    # ---------- Проверки прав ----------
    def _is_viewer(self, request):
        """Проверка, является ли пользователь просмотрщиком"""
        return request.user.groups.filter(name="Просмотрщик").exists()

    def get_actions(self, request):
        """Скрываем выпадающий список действий для просмотрщика"""
        if self._is_viewer(request):
            return {}
        return super().get_actions(request)

    def has_add_permission(self, request):
        if self._is_viewer(request):
            return False
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_viewer(request):
            return False
        return super().has_delete_permission(request, obj)

    # ---------- Колонки ----------
    def user_link(self, obj):
        """Ссылка на пользователя"""
        url = reverse("admin:users_customuser_change", args=[obj.user.id])
        full_name = f"{obj.user.last_name} {obj.user.first_name} {obj.user.patronymic or ''}".strip()
        return mark_safe(f'<a href="{url}">{full_name or obj.user.username}</a>')

    user_link.short_description = "Пользователь"
    user_link.admin_order_field = "user__last_name"

    def organization_link(self, obj):
        """Ссылка на организацию"""
        if obj.organization:
            url = reverse(
                "admin:organizations_organization_change", args=[obj.organization.id]
            )
            return mark_safe(f'<a href="{url}">{obj.organization.short_name}</a>')
        return mark_safe('<span class="text-muted">Безработный</span>')

    organization_link.short_description = "Организация"
    organization_link.admin_order_field = "organization__short_name"

    def position_level_display(self, obj):
        """Отображение категории должности"""
        return obj.get_position_level_display()

    position_level_display.short_description = "Категория должности"
    position_level_display.admin_order_field = "position_level"

    @admin.display(description="Анкета")
    def profile_complete_badge(self, obj):
        if obj.is_profile_complete():
            return mark_safe(
                '<span style="color:#10b981;font-weight:600;">Заполнена</span>'
            )
        return mark_safe(
            '<span style="color:#ef4444;font-weight:600;">Не заполнена</span>'
        )

    @admin.display(description="Полный профиль")
    def full_profile_link(self, obj):
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[obj.id])
        return mark_safe(
            f'<a class="button" href="{url}" '
            f'style="padding:4px 10px;background:#4F46E5;color:#fff;'
            f'border-radius:4px;text-decoration:none;font-size:12px;">'
            f"Открыть</a>"
        )
