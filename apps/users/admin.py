# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "last_name",
            "first_name",
            "patronymic",
            "snils",
            "birthday",
            "user_type",
            "esia_verified",
            "organization__inn",
            "organization__short_name",
        )

    def dehydrate_organization__inn(self, user):
        return user.organization.inn if user.organization else ""

    def dehydrate_organization__short_name(self, user):
        return user.organization.short_name if user.organization else ""


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    """
    Админка для кастомной модели пользователя
    """

    resource_class = CustomUserResource

    list_display = (
        "username",
        "email",
        "last_name",
        "first_name",
        "patronymic",
        "user_type",
        "organization_link",
        # "esia_verified",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "user_type",
        # "esia_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "patronymic",
        "snils",
        "esia_id",
        "organization__inn",
        "organization__short_name",
    )

    list_editable = ("user_type", "is_active")

    ordering = ("-date_joined",)

    list_per_page = 25

    # actions = ["make_esia_verified", "make_not_verified"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "patronymic",
                    "email",
                    "birthday",
                    "snils",
                )
            },
        ),
        (
            _("Organization info"),
            {
                "fields": ("organization",),
                "classes": ("collapse",),
            },
        ),
        # (
        #     _("ESIA info"),
        #     {
        #         "fields": ("esia_id", "esia_verified", "user_type"),
        #         "classes": ("collapse",),
        #     },
        # ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "last_name",
                    "first_name",
                    "email",
                    "user_type",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined", "esia_verified")

    def organization_link(self, obj):
        """Ссылка на организацию"""
        if obj.organization:
            url = reverse(
                "admin:organizations_organization_change", args=[obj.organization.id]
            )
            return mark_safe(f'<a href="{url}">{obj.organization.short_name}</a>')
        return "-"

    organization_link.short_description = "Организация"
    organization_link.admin_order_field = "organization__short_name"

    def make_esia_verified(self, request, queryset):
        updated = queryset.update(esia_verified=True)
        self.message_user(
            request, f"{updated} пользователей отмечены как подтвержденные через ЕСИА"
        )

    make_esia_verified.short_description = "Отметить как подтвержденных через ЕСИА"

    def make_not_verified(self, request, queryset):
        updated = queryset.update(esia_verified=False)
        self.message_user(
            request, f"{updated} пользователей отмечены как неподтвержденные"
        )

    make_not_verified.short_description = "Снять отметку о подтверждении через ЕСИА"
