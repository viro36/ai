from django.contrib import admin
from .models import Question, TechnicalRequirement


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


@admin.register(TechnicalRequirement)
class TechnicalRequirementAdmin(admin.ModelAdmin):
    list_display = ["id", "employer", "universities_count", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["employer__username", "employer__last_name"]
    filter_horizontal = ["universities"]
    readonly_fields = ["created_at", "updated_at"]
