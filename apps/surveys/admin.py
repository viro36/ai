from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from io import StringIO
import tempfile

from .management.commands.import_survey_from_excel import Command
from .models import (
    SurveyCategory,
    SurveyBlock,
    ScaleLabel,
    SurveyQuestion,
    UserSurveyResponse,
    SurveySession,
    SurveyInterpretation,
    DigCompResult,
    RiasacResult,
    Big5Result,
    GardnerResult,
)


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1
    fields = ("text", "q_number", "is_active")
    ordering = ("q_number",)


class SurveyBlockInline(admin.TabularInline):
    model = SurveyBlock
    extra = 1
    fields = ("title", "description", "order", "is_active")
    ordering = ("order",)
    show_change_link = True


class ImportExcelForm(forms.Form):
    excel_file = forms.FileField(label="Excel файл")


@admin.register(SurveyCategory)
class SurveyCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "blocks_count",
        "questions_count",
        "sessions_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description", "instruction_text")
    list_editable = ("is_active",)
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Основная информация", {"fields": ("name", "description", "is_active")}),
        (
            "Отображение",
            {
                "fields": ("instruction_text", "result_description"),
                "classes": ("collapse",),
                "description": "Инструкция отображается под каждым вопросом. Описание результатов отображается в результатах после графика (поддерживает HTML).",
            },
        ),
        ("Системное", {"fields": ("created_at",), "classes": ("collapse",)}),
    )
    inlines = [SurveyBlockInline]

    def blocks_count(self, obj):
        return obj.blocks.filter(is_active=True).count()

    blocks_count.short_description = "Количество блоков"

    def questions_count(self, obj):
        total = 0
        for block in obj.blocks.filter(is_active=True):
            total += block.questions.filter(is_active=True).count()
        return total

    questions_count.short_description = "Количество вопросов"

    def sessions_count(self, obj):
        return obj.sessions.count()

    sessions_count.short_description = "Количество прохождений"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-excel/", self.import_excel, name="import_excel"),
        ]
        return custom_urls + urls

    def import_excel(self, request):
        if request.method == "POST":
            form = ImportExcelForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES["excel_file"]

                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    for chunk in excel_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                command = Command()
                out = StringIO()
                command.stdout = out
                command.stderr = out

                try:
                    command.handle(file_path=tmp_path, force=True, quiet=True)
                    self.message_user(
                        request, "Опрос успешно импортирован!", messages.SUCCESS
                    )
                except Exception as e:
                    self.message_user(
                        request, f"Ошибка импорта: {str(e)}", messages.ERROR
                    )

                return redirect("admin:surveys_surveycategory_changelist")
        else:
            form = ImportExcelForm()

        context = {
            "form": form,
            "title": "Импорт опроса из Excel",
        }
        return render(request, "admin/surveys/import_excel.html", context)


@admin.register(SurveyBlock)
class SurveyBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "order", "questions_count", "is_active")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("title", "description")
    list_editable = ("order", "is_active")
    inlines = [SurveyQuestionInline]

    def questions_count(self, obj):
        return obj.questions.filter(is_active=True).count()

    questions_count.short_description = "Количество вопросов"


@admin.register(ScaleLabel)
class ScaleLabelAdmin(admin.ModelAdmin):
    list_display = ("category", "scale_value", "label")
    list_filter = ("category",)
    list_editable = ("label",)
    search_fields = ("label", "category__name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ("text_preview", "block", "q_number", "responses_count", "is_active")
    list_filter = ("block__category", "block", "is_active", "created_at")
    search_fields = ("text",)
    list_editable = ("q_number", "is_active")

    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    text_preview.short_description = "Вопрос"

    def responses_count(self, obj):
        return obj.responses.count()

    responses_count.short_description = "Ответов"


@admin.register(SurveyInterpretation)
class SurveyInterpretationAdmin(admin.ModelAdmin):
    list_display = ("survey_type", "code", "user_type", "title", "is_active", "order")
    list_filter = ("survey_type", "user_type", "is_active")
    search_fields = ("title", "code", "description")
    list_editable = ("order", "is_active")
    list_per_page = 50

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "survey_type",
                    "code",
                    "user_type",
                    "title",
                    "is_active",
                    "order",
                )
            },
        ),
        ("Контент", {"fields": ("description", "recommendations", "fields_list")}),
        (
            "Для Big5 (опционально)",
            {
                "fields": ("high_description", "low_description"),
                "classes": ("collapse",),
            },
        ),
        ("Оформление", {"fields": ("color",)}),
        (
            "Важные замечания",
            {"fields": ("important_notes",), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("survey_type", "order", "code")


@admin.register(UserSurveyResponse)
class UserSurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "score", "created_at")
    list_filter = ("score", "question__block__category", "created_at")
    search_fields = ("user__username", "user__email", "question__text")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SurveySession)
class SurveySessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "category",
        "status",
        "progress",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "category", "started_at")
    search_fields = ("user__username", "user__email", "category__name")
    readonly_fields = ("progress", "started_at", "completed_at")

    def progress(self, obj):
        return f"{obj.progress}%"

    progress.short_description = "Прогресс"


@admin.register(DigCompResult)
class DigCompResultAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session__user__username", "session__user__email")
    readonly_fields = (
        "session",
        "area1_score",
        "area2_score",
        "area3_score",
        "area4_score",
        "area5_score",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(RiasacResult)
class RiasacResultAdmin(admin.ModelAdmin):
    list_display = ("session", "career_code", "created_at")
    list_filter = ("career_code", "created_at")
    search_fields = ("session__user__username", "session__user__email", "career_code")
    readonly_fields = (
        "session",
        "r_score",
        "i_score",
        "a_score",
        "s_score",
        "e_score",
        "c_score",
        "career_code",
        "dominant_types",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(Big5Result)
class Big5ResultAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session__user__username", "session__user__email")
    readonly_fields = (
        "session",
        "extraversion_score",
        "agreeableness_score",
        "conscientiousness_score",
        "neuroticism_score",
        "openness_score",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(GardnerResult)
class GardnerResultAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")
    list_filter = ("created_at",)
    search_fields = ("session__user__username", "session__user__email")
    readonly_fields = (
        "session",
        "linguistic_score",
        "logical_score",
        "spatial_score",
        "musical_score",
        "kinesthetic_score",
        "interpersonal_score",
        "intrapersonal_score",
        "naturalistic_score",
        "created_at",
    )

    def has_add_permission(self, request):
        return False
