from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class EmployeeDisplayMixin:
    """
    Отображение ФИО работника, курса и трудового статуса.
    Пути к полям задаются атрибутами `employee_path` и `course_path`.
    """

    employee_path = "user"
    course_path = "course"

    def _resolve(self, obj, path):
        target = obj
        for part in path.split("__"):
            target = getattr(target, part)
        return target

    def employee_name(self, obj):
        user = self._resolve(obj, self.employee_path)
        parts = [user.last_name, user.first_name]
        if user.patronymic:
            parts.append(user.patronymic)
        name = " ".join(p for p in parts if p) or user.username
        url = reverse("admin:users_customuser_change", args=[user.pk])
        return format_html('<a href="{}">{}</a>', url, name)

    employee_name.short_description = "ФИО работника"
    employee_name.admin_order_field = "user__last_name"

    def course_title(self, obj):
        course = self._resolve(obj, self.course_path)
        url = reverse("admin:courses_course_change", args=[course.pk])
        return format_html('<a href="{}">{}</a>', url, course.title)

    course_title.short_description = "Курс"
    course_title.admin_order_field = "course__title"

    def employment_status_display(self, obj):
        user = self._resolve(obj, self.employee_path)
        profile = getattr(user, "employee_profile", None)
        if profile is None:
            return "—"
        if profile.is_unemployed:
            return mark_safe('<span style="color:#b00;">Безработный</span>')
        if profile.is_svo_participant:
            return mark_safe('<span style="color:#b06000;">Участник СВО</span>')
        if profile.organization_id:
            url = reverse(
                "admin:organizations_organization_change",
                args=[profile.organization_id],
            )
            return format_html(
                '<a href="{}">{}</a>', url, profile.organization.short_name
            )
        return "—"

    employment_status_display.short_description = "Трудовой статус"


class SelectedCourseDisplayMixin(EmployeeDisplayMixin):
    """Для SelectedCourseAdmin: пути user__, course__."""


class ApprovedCourseDisplayMixin(EmployeeDisplayMixin):
    """Для ApprovedSelectedCourseAdmin: пути selected_course__user__, selected_course__course__."""

    employee_path = "selected_course__user"
    course_path = "selected_course__course"

    def employee_name(self, obj):
        return super().employee_name(obj)

    employee_name.short_description = "ФИО работника"
    employee_name.admin_order_field = "selected_course__user__last_name"

    def course_title(self, obj):
        return super().course_title(obj)

    course_title.short_description = "Курс"
    course_title.admin_order_field = "selected_course__course__title"
