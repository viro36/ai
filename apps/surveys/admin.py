from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from io import StringIO
import tempfile

from .management.commands.import_survey_from_excel import Command
from .models import (
    EducationProgram,
    GeneralizedLaborFunction,
    ProfessionalStandard,
    ProfessionalStandardProgram,
    RiasecCodeInterpretation,
    SurveyCategory,
    SurveyBlock,
    ScaleLabel,
    SurveyQuestion,
    SurveyQuestionOption,
    UserSurveyResponse,
    SurveySession,
    SurveyInterpretation,
    DigCompResult,
    RiasacResult,
    Big5Result,
    GardnerResult,
    DiagnosticKitResult,
)

# ---------------------------------------------------------------------------
# Опросы: категории, блоки, вопросы, шкалы, опции
# ---------------------------------------------------------------------------


class SurveyQuestionOptionInline(admin.TabularInline):
    model = SurveyQuestionOption
    extra = 0
    fields = ("order", "text", "is_correct")
    ordering = ("order",)
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответа"


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1
    fields = ("text", "q_number", "is_active")
    ordering = ("q_number",)
    show_change_link = True


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
        "target_organization_type",
        "positions_count",
        "blocks_count",
        "questions_count",
        "sessions_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "target_organization_type", "created_at")
    search_fields = ("name", "description", "instruction_text")
    list_editable = ("is_active",)
    readonly_fields = ("created_at",)
    filter_horizontal = ("target_positions",)

    fieldsets = (
        ("Основная информация", {"fields": ("name", "description", "is_active")}),
        (
            "Аудитория",
            {
                "fields": (
                    "target_user_types",
                    "target_organization_type",
                    "target_positions",
                ),
                "description": (
                    "Пустые поля = опрос доступен всем. "
                    "target_user_types — JSON-список user_type, "
                    'например: ["employee"].'
                ),
            },
        ),
        (
            "Отображение",
            {
                "fields": ("instruction_text", "result_description"),
                "classes": ("collapse",),
                "description": (
                    "Инструкция отображается под каждым вопросом. "
                    "Описание результатов отображается в результатах после графика "
                    "(поддерживает HTML)."
                ),
            },
        ),
        ("Системное", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    inlines = [SurveyBlockInline]

    def blocks_count(self, obj):
        return obj.blocks.filter(is_active=True).count()

    blocks_count.short_description = "Блоков"

    def questions_count(self, obj):
        total = 0
        for block in obj.blocks.filter(is_active=True):
            total += block.questions.filter(is_active=True).count()
        return total

    questions_count.short_description = "Вопросов"

    def sessions_count(self, obj):
        return obj.sessions.count()

    sessions_count.short_description = "Прохождений"

    def positions_count(self, obj):
        return obj.target_positions.count()

    positions_count.short_description = "Должностей"

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
                        request,
                        "Опрос успешно импортирован!",
                        messages.SUCCESS,
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Ошибка импорта: {str(e)}",
                        messages.ERROR,
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
    list_display = (
        "text_preview",
        "block",
        "q_number",
        "options_count",
        "responses_count",
        "is_active",
    )
    list_filter = ("block__category", "block", "is_active", "created_at")
    search_fields = ("text",)
    list_editable = ("q_number", "is_active")
    inlines = (SurveyQuestionOptionInline,)

    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text

    text_preview.short_description = "Вопрос"

    def options_count(self, obj):
        return obj.options.count()

    options_count.short_description = "Вариантов"

    def responses_count(self, obj):
        return obj.responses.count()

    responses_count.short_description = "Ответов"


@admin.register(SurveyQuestionOption)
class SurveyQuestionOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "text_preview", "is_correct")
    list_filter = ("is_correct", "question__block__category")
    search_fields = ("text", "question__text")
    ordering = ("question", "order")
    list_editable = ("order", "is_correct")

    def text_preview(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    text_preview.short_description = "Текст варианта"


# ---------------------------------------------------------------------------
# Интерпретации и результаты опросов
# ---------------------------------------------------------------------------


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
    list_display = ("user", "question", "score", "selected_option", "created_at")
    list_filter = ("score", "question__block__category", "created_at")
    search_fields = ("user__username", "user__email", "question__text")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("selected_option",)


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


@admin.register(DiagnosticKitResult)
class DiagnosticKitResultAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "work1_score",
        "work2_score",
        "work3_score",
        "work4_score",
        "total_score",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("session__user__username", "session__user__email")
    readonly_fields = (
        "session",
        "work1_score",
        "work2_score",
        "work3_score",
        "work4_score",
        "total_score",
        "created_at",
    )

    def has_add_permission(self, request):
        return False


# ---------------------------------------------------------------------------
# RIASEC-коды
# ---------------------------------------------------------------------------


@admin.register(RiasecCodeInterpretation)
class RiasecCodeInterpretationAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "dominant",
        "secondary",
        "tertiary",
        "is_active",
        "updated_at",
    )
    list_filter = ("dominant", "is_active")
    search_fields = ("code", "description", "professions")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")


# ---------------------------------------------------------------------------
# Профстандарты, ОТФ, ФГОС
# ---------------------------------------------------------------------------


class GeneralizedLaborFunctionInline(admin.TabularInline):
    model = GeneralizedLaborFunction
    extra = 1
    fields = ("code", "name", "qualification_level", "order", "is_active")
    ordering = ("order",)
    show_change_link = True


class ProfessionalStandardProgramInline(admin.TabularInline):
    model = ProfessionalStandardProgram
    extra = 1
    fields = ("education_program", "order")
    autocomplete_fields = ("education_program",)
    ordering = ("order",)


@admin.register(ProfessionalStandard)
class ProfessionalStandardAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "education_level", "is_active", "updated_at")
    list_filter = ("education_level", "is_active")
    search_fields = ("code", "name")
    filter_horizontal = ("riasec_codes",)
    inlines = (GeneralizedLaborFunctionInline, ProfessionalStandardProgramInline)
    ordering = ("education_level", "code")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Основная информация",
            {"fields": ("code", "name", "education_level", "is_active")},
        ),
        (
            "Коды Холланда",
            {
                "fields": ("riasec_codes",),
                "description": "Выберите коды RIASEC, которым соответствует этот профстандарт.",
            },
        ),
        (
            "Системное",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(GeneralizedLaborFunction)
class GeneralizedLaborFunctionAdmin(admin.ModelAdmin):
    list_display = (
        "professional_standard",
        "code",
        "name",
        "qualification_level",
        "order",
        "is_active",
    )
    list_filter = ("professional_standard__education_level", "is_active")
    search_fields = ("code", "name", "professional_standard__code")
    autocomplete_fields = ("professional_standard",)
    ordering = ("professional_standard", "order", "code")
    list_editable = ("order", "is_active")


@admin.register(EducationProgram)
class EducationProgramAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "education_level", "is_active", "updated_at")
    list_filter = ("education_level", "is_active")
    search_fields = ("code", "name")
    ordering = ("education_level", "code")
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProfessionalStandardProgram)
class ProfessionalStandardProgramAdmin(admin.ModelAdmin):
    list_display = ("professional_standard", "education_program", "order")
    list_filter = ("professional_standard__education_level",)
    search_fields = (
        "professional_standard__code",
        "professional_standard__name",
        "education_program__code",
        "education_program__name",
    )
    autocomplete_fields = ("professional_standard", "education_program")
    ordering = ("professional_standard", "order")
    list_editable = ("order",)
