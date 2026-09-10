from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    RecommendationTask,
    SelectedCourse,
    EmployerRecommendation,
)


@admin.register(CourseRecommendation)
class CourseRecommendationAdmin(admin.ModelAdmin):
    """Админка для рекомендаций курсов"""

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

    def relevance_score_display(self, obj):
        """Отображение релевантности в процентах"""
        return f"{obj.get_relevance_percent()}%"

    relevance_score_display.short_description = "Релевантность"
    relevance_score_display.admin_order_field = "relevance_score"

    fieldsets = (
        ("Основное", {"fields": ("user", "course", "session")}),
        ("Оценка", {"fields": ("reason", "relevance_score", "order", "is_viewed")}),
        ("Системное", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(RecommendationTask)
class RecommendationTaskAdmin(admin.ModelAdmin):
    """Админка для задач генерации рекомендаций"""

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

    fieldsets = (
        ("Основное", {"fields": ("user", "status", "task_id")}),
        ("Ошибка", {"fields": ("error_message",), "classes": ("collapse",)}),
        (
            "Системное",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(SelectedCourse)
class SelectedCourseAdmin(admin.ModelAdmin):
    """Админка для выбранных курсов"""

    list_display = (
        "id",
        "user",
        "course",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "user__username",
        "user__email",
        "user__last_name",
        "user__first_name",
        "course__title",
    )
    readonly_fields = ("created_at",)

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

    fieldsets = (
        ("Основное", {"fields": ("user", "course")}),
        ("Системное", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(ApprovedSelectedCourse)
class ApprovedSelectedCourseAdmin(admin.ModelAdmin):
    list_display = ("selected_course", "status", "approved_by", "approved_at")
    list_filter = ("status", "approved_at")
    search_fields = (
        "selected_course__user__username",
        "selected_course__course__title",
    )
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("status",)

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


@admin.register(EmployerRecommendation)
class EmployerRecommendationAdmin(admin.ModelAdmin):
    """Админка для рекомендаций от работодателя"""

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

    fieldsets = (
        ("Основное", {"fields": ("employer", "employee", "course")}),
        ("Дополнительно", {"fields": ("reason", "is_viewed")}),
        (
            "Системное",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
