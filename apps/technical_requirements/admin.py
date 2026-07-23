from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import (
    Question,
    TechnicalRequirement,
    RequirementStatus,
    TechnicalRequirementUniversity,
)


@admin.register(RequirementStatus)
class RequirementStatusAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "color_display", "color", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    list_editable = ("name", "color", "order", "is_active")
    ordering = ("order", "code")

    def color_display(self, obj):
        return mark_safe(
            f'<span style="display: inline-block; width: 20px; height: 20px; '
            f'background-color: {obj.color}; border-radius: 4px; border: 1px solid #ddd;"></span>'
        )

    color_display.short_description = "Цвет"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["order", "text", "question_type", "is_required", "is_active"]
    list_filter = ["question_type", "is_required", "is_active"]
    search_fields = ["text"]
    ordering = ["order"]
    fieldsets = (
        (
            "Основное",
            {"fields": ("order", "text", "question_type", "is_required", "is_active")},
        ),
        ("Настройки", {"fields": ("options", "placeholder", "help_text")}),
        (
            "Условное отображение",
            {"fields": ("depends_on", "depends_value"), "classes": ("collapse",)},
        ),
    )


class TechnicalRequirementUniversityInline(admin.TabularInline):
    model = TechnicalRequirementUniversity
    extra = 1
    fields = ("university", "status")
    raw_id_fields = ("university",)


@admin.register(TechnicalRequirement)
class TechnicalRequirementAdmin(admin.ModelAdmin):
    list_display = ["id", "employer", "universities_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["employer__username", "employer__last_name"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [TechnicalRequirementUniversityInline]
    fieldsets = (
        ("Основное", {"fields": ("employer",)}),
        (
            "Ответы",
            {
                "fields": ("answers",),
                "classes": ("collapse",),
            },
        ),
        (
            "Системное",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def _is_viewer(self, request):
        return request.user.groups.filter(name="Просмотрщик").exists()

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

    def get_actions(self, request):
        if self._is_viewer(request):
            return {}
        return super().get_actions(request)

    def universities_count(self, obj):
        return obj.university_statuses.count()

    universities_count.short_description = "Количество ВУЗов"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Добавляем кнопку "Создать ТЗ через форму"
        extra_context["create_tech_req_url"] = reverse("technical_requirements:create")
        return super().changelist_view(request, extra_context=extra_context)
