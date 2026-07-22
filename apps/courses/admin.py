from django.contrib import admin
from django.shortcuts import redirect, get_object_or_404
from django.urls import path
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from .models import Course, Category
from .tasks import (
    parse_vgltu_courses,
    parse_vspu_courses,
    parse_vsuet_courses,
    parse_vsu_courses,
    parse_vstu_courses,
    parse_vepi_courses,
    parse_vgas_courses,
    parse_vivt_courses,
    parse_all_courses,
)


class CourseResource(resources.ModelResource):
    FIELD_HEADERS = {
        "title": "Название курса",
        "organization__short_name": "Организация",
        "organization__inn": "ИНН организации",
        "categories": "Категории",
        "program_type": "Тип программы",
        "duration_hours": "Объём (часы)",
        "duration_weeks": "Продолжительность (недели)",
        "study_mode": "Режим обучения",
        "format": "Форма обучения",
        "teachers": "Преподаватели",
        "target_audience": "Целевая аудитория",
        "topics": "Содержание программы",
        "start_dates": "Даты начала обучения",
        "price": "Стоимость",
        "field_of_study": "Направление",
        "url": "Ссылка на курс",
        "last_parsed": "Дата добавления",
        "is_deleted": "Удалён",
        "deleted_at": "Дата удаления",
    }

    class Meta:
        model = Course
        fields = (
            "title",
            "organization__short_name",
            "organization__inn",
            "categories",
            "program_type",
            "duration_hours",
            "duration_weeks",
            "study_mode",
            "format",
            "teachers",
            "target_audience",
            "topics",
            "start_dates",
            "price",
            "field_of_study",
            "url",
            "last_parsed",
            "is_deleted",
            "deleted_at",
        )
        export_order = fields

    def get_export_headers(self, selected_fields=None):
        if selected_fields:
            return [self.FIELD_HEADERS.get(field, field) for field in selected_fields]
        return [
            self.FIELD_HEADERS.get(field, field) for field in self._meta.export_order
        ]

    def dehydrate_organization__short_name(self, course):
        return course.organization.short_name if course.organization else ""

    def dehydrate_organization__inn(self, course):
        return course.organization.inn if course.organization else ""

    def dehydrate_categories(self, course):
        return "; ".join([cat.name for cat in course.categories.all()])

    def dehydrate_is_deleted(self, course):
        return "Да" if course.is_deleted else "Нет"


class ParseActionsMixin:
    """Mixin с действиями для парсинга"""

    PARSER_TASKS = {
        "vsuet": {"name": "ВГУИТ", "task": parse_vsuet_courses},
        "vsu": {"name": "ВГУ", "task": parse_vsu_courses},
        "vstu": {"name": "ВГТУ", "task": parse_vstu_courses},
        "vgltu": {"name": "ВГЛТУ", "task": parse_vgltu_courses},
        "vspu": {"name": "ВГПУ", "task": parse_vspu_courses},
        "vepi": {"name": "ВЭПИ", "task": parse_vepi_courses},
        "vgas": {"name": "ВГАС", "task": parse_vgas_courses},
        "vivt": {"name": "ВИВТ", "task": parse_vivt_courses},
    }

    def _is_viewer(self, request):
        """Проверка, является ли пользователь просмотрщиком"""
        return request.user.groups.filter(name="Просмотрщик").exists()

    def _check_viewer_permission(self, request):
        if self._is_viewer(request):
            raise PermissionDenied("У вас нет прав на выполнение этого действия")

    def _run_parser(self, request, parser_key):
        self._check_viewer_permission(request)
        parser_info = self.PARSER_TASKS.get(parser_key)
        if not parser_info:
            messages.error(request, f"Парсер {parser_key} не найден")
            return redirect(request.META.get("HTTP_REFERER", "/admin/"))

        task = parser_info["task"].delay()
        messages.success(
            request,
            f"Парсинг {parser_info['name']} запущен в фоне! (ID задачи: {task.id})",
        )
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    def get_urls(self):
        urls = super().get_urls() if hasattr(super(), "get_urls") else []
        custom_urls = []

        for parser_key in self.PARSER_TASKS:

            def make_view(key):
                def view(request):
                    return self._run_parser(request, key)

                return view

            custom_urls.append(
                path(
                    f"parse-{parser_key}/",
                    make_view(parser_key),
                    name=f"parse_{parser_key}",
                )
            )

        custom_urls.append(path("parse-all/", self.parse_all, name="parse_all"))
        return custom_urls + urls

    def parse_all(self, request):
        self._check_viewer_permission(request)
        task = parse_all_courses.delay()
        messages.success(
            request, f"Парсинг всех источников запущен в фоне! (ID задачи: {task.id})"
        )
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))


class SoftDeleteFilter(admin.SimpleListFilter):
    title = "Статус курсов"
    parameter_name = "course_status"

    def lookups(self, request, model_admin):
        return (
            ("active", "Активные"),
            ("deleted", "Удалённые (в корзине)"),
            ("all", "Все курсы"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "active":
            return queryset.filter(is_deleted=False)
        if value == "deleted":
            return queryset.filter(is_deleted=True)
        if value == "all":
            return queryset
        return queryset


@admin.register(Course)
class CourseAdmin(ExportMixin, ParseActionsMixin, admin.ModelAdmin):
    resource_class = CourseResource
    list_display = (
        "title",
        "organization",
        "categories_display",
        "program_type",
        "duration_hours",
        "format",
        "status_display",
        "last_parsed",
    )
    list_filter = (
        "organization",
        "program_type",
        "format",
        "categories",
        SoftDeleteFilter,
    )
    search_fields = ("title", "description", "organization__short_name")
    readonly_fields = ("last_parsed", "deleted_at")
    filter_horizontal = ("categories",)

    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]

    actions = ["soft_delete_action", "restore_action", "hard_delete_action"]

    def _is_viewer(self, request):
        return request.user.groups.filter(name="Просмотрщик").exists()

    def _check_viewer_permission(self, request):
        if self._is_viewer(request):
            raise PermissionDenied("У вас нет прав на выполнение этого действия")

    @admin.display(description="Категории")
    def categories_display(self, obj):
        categories = obj.categories.all()
        if not categories:
            return mark_safe('<span style="color: #6c757d;">—</span>')

        badges = []
        for cat in categories[:5]:
            badges.append(
                f'<span style="display: inline-block; background: #e9ecef; '
                f"padding: 2px 8px; border-radius: 12px; font-size: 11px; "
                f'margin: 1px 2px; color: #495057;">{cat.name}</span>'
            )

        if categories.count() > 5:
            badges.append(
                f'<span style="display: inline-block; background: #dee2e6; '
                f"padding: 2px 8px; border-radius: 12px; font-size: 11px; "
                f'margin: 1px 2px; color: #495057;">+{categories.count() - 5}</span>'
            )

        return mark_safe(" ".join(badges))

    @admin.display(description="Статус")
    def status_display(self, obj):
        if obj.is_deleted:
            return mark_safe(
                '<span style="color: #dc3545; font-weight: bold;">Корзина</span>'
            )
        return mark_safe(
            '<span style="color: #28a745; font-weight: bold;">Активен</span>'
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("categories")

    def soft_delete_action(self, request, queryset):
        self._check_viewer_permission(request)
        count = queryset.filter(is_deleted=False).count()
        queryset.filter(is_deleted=False).update(
            is_deleted=True, deleted_at=timezone.now()
        )
        self.message_user(
            request, f"{count} курс(ов) перемещён(о) в корзину.", messages.SUCCESS
        )

    soft_delete_action.short_description = "Переместить в корзину"

    def restore_action(self, request, queryset):
        self._check_viewer_permission(request)
        count = queryset.filter(is_deleted=True).count()
        queryset.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        self.message_user(
            request, f"{count} курс(ов) восстановлен(о) из корзины.", messages.SUCCESS
        )

    restore_action.short_description = "Восстановить из корзины"

    def hard_delete_action(self, request, queryset):
        self._check_viewer_permission(request)
        count = queryset.count()
        for course in queryset:
            course.categories.clear()
            course.delete()
        self.message_user(
            request,
            f"{count} курс(ов) полностью удален(о) из базы данных.",
            messages.WARNING,
        )

    hard_delete_action.short_description = "Полностью удалить навсегда"

    def get_actions(self, request):
        """Скрываем выпадающий список действий для просмотрщика"""
        actions = super().get_actions(request)
        if self._is_viewer(request):
            return {}  # Возвращаем пустой словарь - действий нет
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_urls(self):
        """Скрываем URL для парсинга у просмотрщика"""
        # Получаем базовые URL без кастомных
        urls = super().get_urls()
        # Кастомные URL добавляем всегда, но доступ к ним будет закрыт через _check_viewer_permission
        custom_urls = [
            path(
                "restore/<int:course_id>/",
                self.restore_single_course,
                name="restore_course",
            ),
            path(
                "soft-delete/<int:course_id>/",
                self.soft_delete_single_course,
                name="soft_delete_course",
            ),
            path(
                "hard-delete/<int:course_id>/",
                self.hard_delete_single_course,
                name="hard_delete_course",
            ),
        ]
        return custom_urls + urls

    def restore_single_course(self, request, course_id):
        self._check_viewer_permission(request)
        course = get_object_or_404(Course, id=course_id, is_deleted=True)
        course.is_deleted = False
        course.deleted_at = None
        course.save()
        self.message_user(
            request, f'Курс "{course.title}" восстановлен из корзины.', messages.SUCCESS
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def soft_delete_single_course(self, request, course_id):
        self._check_viewer_permission(request)
        course = get_object_or_404(Course, id=course_id, is_deleted=False)
        course.is_deleted = True
        course.deleted_at = timezone.now()
        course.save()
        self.message_user(
            request, f'Курс "{course.title}" перемещён в корзину.', messages.SUCCESS
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def hard_delete_single_course(self, request, course_id):
        self._check_viewer_permission(request)
        course = get_object_or_404(Course, id=course_id)
        title = course.title
        course.categories.clear()
        course.delete()
        self.message_user(
            request,
            f'Курс "{title}" полностью удалён из базы данных.',
            messages.WARNING,
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def delete_model(self, request, obj):
        self._check_viewer_permission(request)
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save()
        self.message_user(
            request, f'Курс "{obj.title}" перемещён в корзину.', messages.SUCCESS
        )

    def delete_queryset(self, request, queryset):
        self._check_viewer_permission(request)
        self.soft_delete_action(request, queryset)

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

    def changelist_view(self, request, extra_context=None):
        """Скрываем кнопку "Добавить курс" для просмотрщика"""
        if self._is_viewer(request):
            extra_context = extra_context or {}
            extra_context["show_add_button"] = False
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "courses_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def _is_viewer(self, request):
        return request.user.groups.filter(name="Просмотрщик").exists()

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(courses_count=Count("course"))

    @admin.display(description="Количество курсов")
    def courses_count(self, obj):
        return obj.courses_count

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
