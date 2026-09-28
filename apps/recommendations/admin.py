from django.contrib import admin
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html

from .admin_display import (
    ApprovedCourseDisplayMixin,
    SelectedCourseDisplayMixin,
)
from .admin_filters import (
    ApprovalStatusFilter,
    ApprovedByFilter,
    ApprovedEmploymentFilter,
    SelectedEmploymentFilter,
)
from .admin_mixins import ViewerRestrictedMixin
from .models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    RecommendationTask,
    SelectedCourse,
    EmployerRecommendation,
)


# ============================================================
# CourseRecommendation
# ============================================================
@admin.register(CourseRecommendation)
class CourseRecommendationAdmin(ViewerRestrictedMixin, admin.ModelAdmin):
    """Админка для рекомендаций курсов."""

    list_display = (
        "id",
        "user",
        "course",
        "relevance_score_display",
        "order",
        "is_viewed",
        "created_at",
    )
    list_filter = ("is_viewed", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__last_name",
        "user__first_name",
        "course__title",
    )
    readonly_fields = ("created_at", "relevance_score")
    list_editable = ("order", "is_viewed")

    def relevance_score_display(self, obj):
        return f"{obj.get_relevance_percent()}%"

    relevance_score_display.short_description = "Релевантность"
    relevance_score_display.admin_order_field = "relevance_score"

    fieldsets = (
        ("Основное", {"fields": ("user", "course", "session")}),
        ("Оценка", {"fields": ("reason", "relevance_score", "order", "is_viewed")}),
        ("Системное", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


# ============================================================
# RecommendationTask
# ============================================================
@admin.register(RecommendationTask)
class RecommendationTaskAdmin(ViewerRestrictedMixin, admin.ModelAdmin):
    """Админка для задач генерации рекомендаций."""

    list_display = (
        "id",
        "user",
        "status",
        "task_id",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = (
        "user__username",
        "user__email",
        "user__last_name",
        "user__first_name",
        "task_id",
    )
    readonly_fields = ("created_at", "updated_at", "task_id")
    list_editable = ("status",)

    fieldsets = (
        ("Основное", {"fields": ("user", "status", "task_id")}),
        ("Ошибка", {"fields": ("error_message",), "classes": ("collapse",)}),
        (
            "Системное",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# ============================================================
# SelectedCourse
# ============================================================
@admin.register(SelectedCourse)
class SelectedCourseAdmin(
    ViewerRestrictedMixin,
    SelectedCourseDisplayMixin,
    admin.ModelAdmin,
):
    """Админка для выбранных курсов."""

    list_display = (
        "id",
        "employee_name",
        "course_title",
        "employment_status_display",
        "approval_status_display",
        "created_at",
    )
    list_filter = (
        ApprovalStatusFilter,
        SelectedEmploymentFilter,
        ApprovedByFilter,
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__last_name",
        "user__first_name",
        "user__patronymic",
        "user__organization__short_name",
        "course__title",
    )
    readonly_fields = ("created_at",)
    list_select_related = (
        "user",
        "user__employee_profile",
        "user__employee_profile__organization",
        "course",
        "approval",
    )
    list_per_page = 50
    list_max_show_all = 500
    actions = ["approve_selected", "reject_selected"]

    def approval_status_display(self, obj):
        approval = getattr(obj, "approval", None)
        if approval is None:
            return format_html('<span style="color:#888;">{}</span>', "не рассмотрено")
        colors = {
            "pending": "#b06000",
            "approved": "green",
            "rejected": "#b00",
        }
        color = colors.get(approval.status, "#333")
        url = reverse(
            "admin:recommendations_approvedselectedcourse_change",
            args=[approval.pk],
        )
        return format_html(
            '<a href="{}" style="color:{}; font-weight:bold;">{}</a>',
            url,
            color,
            approval.get_status_display(),
        )

    approval_status_display.short_description = "Статус одобрения"

    @admin.action(description="Одобрить выбранные курсы")
    def approve_selected(self, request, queryset):
        created_count = 0
        updated_count = 0
        for selected in queryset:
            approval, created = ApprovedSelectedCourse.objects.get_or_create(
                selected_course=selected,
                defaults={
                    "status": "approved",
                    "approved_by": request.user,
                    "approved_at": timezone.now(),
                },
            )
            if created:
                created_count += 1
            else:
                approval.status = "approved"
                approval.approved_by = request.user
                approval.approved_at = timezone.now()
                approval.save()
                updated_count += 1
        self.message_user(
            request,
            f"Одобрено: {created_count} новых, {updated_count} обновлено.",
        )

    @admin.action(description="Отклонить выбранные курсы")
    def reject_selected(self, request, queryset):
        created_count = 0
        updated_count = 0
        for selected in queryset:
            approval, created = ApprovedSelectedCourse.objects.get_or_create(
                selected_course=selected,
                defaults={
                    "status": "rejected",
                    "approved_by": request.user,
                    "approved_at": timezone.now(),
                },
            )
            if created:
                created_count += 1
            else:
                approval.status = "rejected"
                approval.approved_by = request.user
                approval.approved_at = timezone.now()
                approval.save()
                updated_count += 1
        self.message_user(
            request,
            f"Отклонено: {created_count} новых, {updated_count} обновлено.",
        )


# ============================================================
# ApprovedSelectedCourse
# ============================================================
@admin.register(ApprovedSelectedCourse)
class ApprovedSelectedCourseAdmin(
    ViewerRestrictedMixin,
    ApprovedCourseDisplayMixin,
    admin.ModelAdmin,
):
    list_display = (
        "id",
        "employee_name",
        "course_title",
        "employment_status_display",
        "status",
        "approved_by_display",
        "approved_at",
    )
    list_filter = ("status", "approved_at", ApprovedEmploymentFilter)
    search_fields = (
        "selected_course__user__username",
        "selected_course__user__last_name",
        "selected_course__user__first_name",
        "selected_course__user__patronymic",
        "selected_course__course__title",
    )
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)
    list_select_related = (
        "selected_course__user",
        "selected_course__user__employee_profile",
        "selected_course__user__employee_profile__organization",
        "selected_course__course",
        "approved_by",
    )

    def approved_by_display(self, obj):
        if not obj.approved_by:
            return "—"
        user = obj.approved_by
        name = user.get_full_name() or user.username
        url = reverse("admin:users_customuser_change", args=[user.pk])
        return format_html('<a href="{}">{}</a>', url, name)

    approved_by_display.short_description = "Кем одобрено"
    approved_by_display.admin_order_field = "approved_by__last_name"


# ============================================================
# EmployerRecommendation
# ============================================================
@admin.register(EmployerRecommendation)
class EmployerRecommendationAdmin(ViewerRestrictedMixin, admin.ModelAdmin):
    """Админка для рекомендаций от работодателя."""

    list_display = (
        "id",
        "employer",
        "employee",
        "course",
        "is_viewed",
        "created_at",
    )
    list_filter = ("is_viewed", "created_at", "updated_at")
    search_fields = (
        "employer__username",
        "employer__email",
        "employer__last_name",
        "employer__first_name",
        "employee__username",
        "employee__email",
        "employee__last_name",
        "employee__first_name",
        "course__title",
    )
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_viewed",)

    fieldsets = (
        ("Основное", {"fields": ("employer", "employee", "course")}),
        ("Дополнительно", {"fields": ("reason", "is_viewed")}),
        (
            "Системное",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
