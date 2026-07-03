from django.contrib import admin
from .models import Question, QuestionOption, GoalSettingResponse


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1
    fields = ("value", "label", "is_custom", "order")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "text", "question_type", "is_required", "is_active")
    list_filter = ("question_type", "is_required", "is_active")
    search_fields = ("text",)
    ordering = ("order",)
    inlines = [QuestionOptionInline]
    fieldsets = (
        (
            "Основная информация",
            {"fields": ("text", "description", "question_type", "order")},
        ),
        (
            "Настройки",
            {
                "fields": (
                    "is_required",
                    "is_active",
                    "max_length",
                    "is_multiple",
                    "has_custom_option",
                    "custom_option_label",
                )
            },
        ),
    )


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "label", "value", "is_custom", "order")
    list_filter = ("question", "is_custom")
    search_fields = ("label", "value")


@admin.register(GoalSettingResponse)
class GoalSettingResponseAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "get_answer_preview", "updated_at")
    list_filter = ("question",)
    search_fields = ("user__username", "user__email", "answer_text")
    readonly_fields = ("updated_at",)

    def get_answer_preview(self, obj):
        if obj.answer_option:
            return obj.answer_option.label
        elif obj.answer_text:
            return (
                obj.answer_text[:50] + "..."
                if len(obj.answer_text) > 50
                else obj.answer_text
            )
        elif obj.answer_date_start and obj.answer_date_end:
            return f"{obj.answer_date_start} - {obj.answer_date_end}"
        return "-"

    get_answer_preview.short_description = "Ответ"
