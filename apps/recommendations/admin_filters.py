from django.contrib import admin

from .models import ApprovedSelectedCourse


class ApprovalStatusFilter(admin.SimpleListFilter):
    """Фильтр по статусу одобрения выбранного курса."""

    title = "Статус одобрения"
    parameter_name = "approval_status"

    def lookups(self, request, model_admin):
        return (
            ("none", "Не рассмотрено"),
            ("pending", "На рассмотрении"),
            ("approved", "Одобрено"),
            ("rejected", "Отклонено"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "none":
            return queryset.filter(approval__isnull=True)
        if v in ("pending", "approved", "rejected"):
            return queryset.filter(approval__status=v)
        return queryset


class SelectedEmploymentFilter(admin.SimpleListFilter):
    """Фильтр по трудовому статусу работника, выбравшего курс.

    Используется в SelectedCourseAdmin — путь через `user__`.
    """

    title = "Трудовой статус"
    parameter_name = "employment"

    def lookups(self, request, model_admin):
        return (
            ("unemployed", "Безработные"),
            ("svo", "Участники СВО"),
            ("employed", "Работающие"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "unemployed":
            return queryset.filter(user__employee_profile__is_unemployed=True)
        if v == "svo":
            return queryset.filter(user__employee_profile__is_svo_participant=True)
        if v == "employed":
            return queryset.filter(
                user__employee_profile__is_unemployed=False,
                user__employee_profile__organization__isnull=False,
            )
        return queryset


class ApprovedEmploymentFilter(admin.SimpleListFilter):
    """Фильтр по трудовому статусу работника.

    Используется в ApprovedSelectedCourseAdmin — путь через `selected_course__user__`.
    """

    title = "Трудовой статус"
    parameter_name = "employment"

    def lookups(self, request, model_admin):
        return (
            ("unemployed", "Безработные"),
            ("svo", "Участники СВО"),
            ("employed", "Работающие"),
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v == "unemployed":
            return queryset.filter(
                selected_course__user__employee_profile__is_unemployed=True
            )
        if v == "svo":
            return queryset.filter(
                selected_course__user__employee_profile__is_svo_participant=True
            )
        if v == "employed":
            return queryset.filter(
                selected_course__user__employee_profile__is_unemployed=False,
                selected_course__user__employee_profile__organization__isnull=False,
            )
        return queryset


class ApprovedByFilter(admin.SimpleListFilter):
    """Фильтр по тому, кто одобрил/отклонил выбранный курс."""

    title = "Кем одобрено"
    parameter_name = "approved_by"

    def lookups(self, request, model_admin):
        from apps.users.models import CustomUser

        ids = ApprovedSelectedCourse.objects.values_list(
            "approved_by", flat=True
        ).distinct()
        return [
            (u.pk, u.get_full_name() or u.username)
            for u in CustomUser.objects.filter(pk__in=ids)
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(approved_by_id=self.value())
        return queryset
