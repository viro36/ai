from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.db.models import Max
from django.utils.html import format_html

from .models import Year, NeedType, Occupation, EconomicActivity, LaborNeed


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ("year",)
    list_display_links = ("year",)
    ordering = ("year",)
    search_fields = ("year",)


@admin.register(NeedType)
class NeedTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_display_links = ("name",)
    search_fields = ("name",)


class LaborNeedInline(admin.TabularInline):
    """Read-only inline со значениями потребности для одного занятия."""

    model = LaborNeed
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("year", "need_type", "economic_activity", "value", "updated_at")
    readonly_fields = ("year", "need_type", "economic_activity", "value", "updated_at")
    ordering = ("-year__year", "need_type", "economic_activity__name")
    classes = ("collapse",)
    verbose_name = "Кадровая потребность"
    verbose_name_plural = "Кадровая потребность"

    def get_queryset(self, request):
        """Показываем только последние 2 года, чтобы не тянуть всё."""
        qs = super().get_queryset(request)
        latest = Year.objects.aggregate(m=Max("year"))["m"]
        if latest is None:
            return qs.none()
        return qs.filter(year__year__gte=latest - 1)


@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "labor_needs_count")
    list_display_links = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)
    list_per_page = 50
    inlines = (LaborNeedInline,)

    @admin.display(description="Записей потребности")
    def labor_needs_count(self, obj):
        return obj.laborneed_set.count()


@admin.register(EconomicActivity)
class EconomicActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "labor_needs_count")
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50

    @admin.display(description="Записей потребности")
    def labor_needs_count(self, obj):
        return obj.laborneed_set.count()


@admin.register(LaborNeed)
class LaborNeedAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "need_type",
        "occupation_code",
        "occupation_name",
        "economic_activity_name",
        "value_display",
        "updated_at",
    )
    list_filter = (
        "year",
        "need_type",
        "economic_activity",
        ("occupation", RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "occupation__code",
        "occupation__name",
        "economic_activity__name",
    )
    autocomplete_fields = ("occupation", "economic_activity")
    list_select_related = ("year", "need_type", "occupation", "economic_activity")

    ordering = ("year", "need_type", "occupation__code")
    list_per_page = 100
    readonly_fields = ("updated_at",)
    show_full_result_count = False

    fieldsets = (
        (None, {"fields": ("year", "need_type", "occupation", "economic_activity")}),
        ("Значение", {"fields": ("value", "source_file", "updated_at")}),
    )

    @admin.display(description="Код занятия", ordering="occupation__code")
    def occupation_code(self, obj):
        return obj.occupation.code

    @admin.display(description="Наименование занятия", ordering="occupation__name")
    def occupation_name(self, obj):
        return obj.occupation.name

    @admin.display(
        description="Вид деятельности",
        ordering="economic_activity__name",
    )
    def economic_activity_name(self, obj):
        return obj.economic_activity.name

    @admin.display(description="Значение", ordering="value")
    def value_display(self, obj):
        return format_html("<b>{}</b>", f"{obj.value:,.2f}".replace(",", " "))
