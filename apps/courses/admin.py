from django.contrib import admin
from django.shortcuts import redirect, get_object_or_404
from django.urls import path
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponseRedirect
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats
from .models import Course, Category
from .parsers.parser_manager import ParserManager


class CourseResource(resources.ModelResource):
    """Ресурс для экспорта/импорта курсов"""

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "organization__short_name",
            "organization__inn",
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

    def dehydrate_organization__short_name(self, course):
        """Название организации"""
        return course.organization.short_name if course.organization else ""

    def dehydrate_organization__inn(self, course):
        """ИНН организации"""
        return course.organization.inn if course.organization else ""

    def dehydrate_categories(self, course):
        """Категории (теги) курса"""
        return ", ".join([cat.name for cat in course.categories.all()])

    def dehydrate_is_deleted(self, course):
        """Статус удаления"""
        return "Да" if course.is_deleted else "Нет"


class ParseActionsMixin:
    """Mixin с действиями для парсинга"""

    def parse_vsuet(self, request):
        ParserManager.run_parser("vsuet", request)
        messages.success(request, "Парсинг ВГУИТ успешно завершён!")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    def parse_vsu(self, request):
        ParserManager.run_parser("vsu", request)
        messages.success(request, "Парсинг ВГУ успешно завершён!")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    def parse_vstu(self, request):
        ParserManager.run_parser("vstu", request)
        messages.success(request, "Парсинг ВГТУ успешно завершён!")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    def parse_all(self, request):
        ParserManager.run_all_parsers(request)
        messages.success(request, "Парсинг всех источников успешно завершён!")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))


class SoftDeleteFilter(admin.SimpleListFilter):
    """Кастомный фильтр для показа активных/удалённых/всех курсов"""

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

        # По умолчанию показываем все курсы
        return queryset


@admin.register(Course)
class CourseAdmin(ExportMixin, ParseActionsMixin, admin.ModelAdmin):
    resource_class = CourseResource
    list_display = (
        "title",
        "organization",
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
        SoftDeleteFilter,
    )
    search_fields = ("title", "description", "organization__short_name")
    readonly_fields = ("last_parsed", "deleted_at")
    filter_horizontal = ("categories",)

    # Настройка экспорта
    formats = [base_formats.CSV, base_formats.XLSX, base_formats.JSON]

    change_list_template = "admin/courses/course/change_list.html"

    # Действия с выбранными объектами
    actions = ["soft_delete_action", "restore_action", "hard_delete_action"]

    def get_queryset(self, request):
        """Показываем все курсы, фильтрация через SoftDeleteFilter"""
        return super().get_queryset(request)

    @admin.display(description="Статус")
    def status_display(self, obj):
        """Отображение статуса удаления в виде цветного бейджа"""
        if obj.is_deleted:
            return mark_safe(
                '<span style="color: #dc3545; font-weight: bold;">Корзина</span>'
            )
        return mark_safe(
            '<span style="color: #28a745; font-weight: bold;">Активен</span>'
        )

    def soft_delete_action(self, request, queryset):
        """Массовое мягкое удаление выбранных курсов"""
        count = queryset.filter(is_deleted=False).count()
        queryset.filter(is_deleted=False).update(
            is_deleted=True, deleted_at=timezone.now()
        )
        self.message_user(
            request, f"{count} курс(ов) перемещён(о) в корзину.", messages.SUCCESS
        )

    soft_delete_action.short_description = "Переместить в корзину"

    def restore_action(self, request, queryset):
        """Массовое восстановление выбранных курсов"""
        count = queryset.filter(is_deleted=True).count()
        queryset.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        self.message_user(
            request, f"{count} курс(ов) восстановлен(о) из корзины.", messages.SUCCESS
        )

    restore_action.short_description = "Восстановить из корзины"

    def hard_delete_action(self, request, queryset):
        """Полное удаление выбранных курсов из БД"""
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
        """Убираем стандартное действие удаления"""
        actions = super().get_actions(request)
        # Удаляем стандартное действие 'delete_selected'
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("parse-vsuet/", self.parse_vsuet, name="parse_vsuet"),
            path("parse-vsu/", self.parse_vsu, name="parse_vsu"),
            path("parse-vstu/", self.parse_vstu, name="parse_vstu"),
            path("parse-all/", self.parse_all, name="parse_all"),
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
        """Восстановление одного курса"""
        course = get_object_or_404(Course, id=course_id, is_deleted=True)
        course.is_deleted = False
        course.deleted_at = None
        course.save()
        self.message_user(
            request, f'Курс "{course.title}" восстановлен из корзины.', messages.SUCCESS
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def soft_delete_single_course(self, request, course_id):
        """Мягкое удаление одного курса"""
        course = get_object_or_404(Course, id=course_id, is_deleted=False)
        course.is_deleted = True
        course.deleted_at = timezone.now()
        course.save()
        self.message_user(
            request, f'Курс "{course.title}" перемещён в корзину.', messages.SUCCESS
        )
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def hard_delete_single_course(self, request, course_id):
        """Полное удаление одного курса"""
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

    # Переопределяем стандартные методы админки
    def delete_model(self, request, obj):
        """Мягкое удаление вместо обычного"""
        obj.is_deleted = True
        obj.deleted_at = timezone.now()
        obj.save()
        self.message_user(
            request, f'Курс "{obj.title}" перемещён в корзину.', messages.SUCCESS
        )

    def delete_queryset(self, request, queryset):
        """Массовое мягкое удаление"""
        self.soft_delete_action(request, queryset)

    def get_list_display(self, request):
        """Динамически меняем отображение для удалённых курсов"""
        list_display = list(super().get_list_display(request))
        # Можно добавить кнопки действий в список
        return list_display


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
