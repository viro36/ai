import logging
from datetime import date
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from .models import District, OrganizationType, Organization
from .dadata_client import get_organization_by_inn

logger = logging.getLogger(__name__)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "organizations_count")
    search_fields = ("short_name", "full_name")
    ordering = ("short_name",)

    def organizations_count(self, obj):
        return obj.organization_set.count()

    organizations_count.short_description = "Кол-во организаций"


@admin.register(OrganizationType)
class OrganizationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "organizations_count")
    search_fields = ("name",)
    ordering = ("name",)

    def organizations_count(self, obj):
        return obj.organization_set.count()

    organizations_count.short_description = "Кол-во организаций"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "short_name",
        "inn",
        "status_colored",
        "district_link",
        "organization_type_link",
        "show_map_link",
    )

    search_fields = ("short_name", "full_name", "inn", "ogrn")
    list_filter = ("status", "organization_type", "district")
    ordering = ("district", "short_name")

    actions = ["update_from_dadata"]

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    ("short_name", "full_name"),
                    ("full_name_without_opf", "short_name_without_opf"),
                    ("inn", "kpp", "kpp_largest", "ogrn", "ogrn_date"),
                    ("org_type", "hid"),
                    ("organization_type", "district"),
                    ("status", "status_code", "coordinates"),
                )
            },
        ),
        (
            "ОПФ (Организационно-правовая форма)",
            {
                "fields": (
                    ("opf_code", "opf_type"),
                    ("opf_full", "opf_short"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "ФИО для ИП",
            {
                "fields": (("fio_surname", "fio_name", "fio_patronymic"),),
                "classes": ("collapse",),
            },
        ),
        (
            "Коды статистики",
            {
                "fields": (
                    ("okpo", "okato", "oktmo"),
                    ("okogu", "okfs", "okved", "okved_type"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Руководство",
            {
                "fields": (("manager_name", "manager_post", "manager_start_date"),),
                "classes": ("collapse",),
            },
        ),
        (
            "Филиалы",
            {
                "fields": (("branch_count", "branch_type"),),
                "classes": ("collapse",),
            },
        ),
        (
            "Даты регистрации",
            {
                "fields": (
                    ("registration_date", "liquidation_date", "actuality_date"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Адрес",
            {
                "fields": (
                    "address_raw",
                    "address_source",
                    "address_qc",
                    ("postal_code", "region", "city"),
                    ("street", "house"),
                ),
            },
        ),
        (
            "Даты",
            {
                "fields": (("created_at", "updated_at"),),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "show_map_link")
    list_per_page = 50

    def status_colored(self, obj):
        if not obj.status:
            return "-"

        colors = {
            "ACTIVE": "green",
            "LIQUIDATING": "orange",
            "LIQUIDATED": "red",
        }
        color = colors.get(obj.status, "gray")

        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">{obj.get_status_display()}</span>'
        )

    status_colored.short_description = "Статус"
    status_colored.admin_order_field = "status"

    def district_link(self, obj):
        if obj.district:
            return mark_safe(
                f'<a href="/admin/organizations/district/{obj.district.id}/change/">{obj.district.short_name}</a>'
            )
        return "-"

    district_link.short_description = "Район"
    district_link.admin_order_field = "district"

    def organization_type_link(self, obj):
        if obj.organization_type:
            return mark_safe(
                f'<a href="/admin/organizations/organizationtype/{obj.organization_type.id}/change/">{obj.organization_type.name}</a>'
            )
        return "-"

    organization_type_link.short_description = "Тип организации"
    organization_type_link.admin_order_field = "organization_type"

    def show_map_link(self, obj):
        if obj.coordinates and "," in obj.coordinates:
            parts = obj.coordinates.split(",")
            if len(parts) == 2:
                lat, lon = parts[0].strip(), parts[1].strip()
                return mark_safe(
                    f'<a href="https://yandex.ru/maps/?ll={lon},{lat}&z=17&pt={lon},{lat}" target="_blank">Открыть на карте</a>'
                )
        return "Нет координат"

    show_map_link.short_description = "Карта"

    def update_from_dadata(self, request, queryset):
        """Массовое обновление организаций из DaData"""
        updated_count = 0
        error_count = 0
        no_data_count = 0

        for org in queryset:
            data = get_organization_by_inn(org.inn, debug=False)

            if not data:
                no_data_count += 1
                continue

            updated = False

            # Основные реквизиты
            if data.get("kpp") and data["kpp"] != org.kpp:
                org.kpp = data["kpp"]
                updated = True

            if data.get("kpp_largest") and data["kpp_largest"] != org.kpp_largest:
                org.kpp_largest = data["kpp_largest"]
                updated = True

            if data.get("ogrn") and data["ogrn"] != org.ogrn:
                org.ogrn = data["ogrn"]
                updated = True

            if data.get("ogrn_date") and data["ogrn_date"] != org.ogrn_date:
                if isinstance(data["ogrn_date"], date):
                    org.ogrn_date = data["ogrn_date"]
                    updated = True
                elif isinstance(data["ogrn_date"], str):
                    from datetime import datetime

                    try:
                        org.ogrn_date = datetime.fromisoformat(
                            data["ogrn_date"].replace("Z", "+00:00")
                        ).date()
                        updated = True
                    except (ValueError, TypeError):
                        pass

            if data.get("hid") and data["hid"] != org.hid:
                org.hid = data["hid"]
                updated = True

            if data.get("org_type") and data["org_type"] != org.org_type:
                org.org_type = data["org_type"]
                updated = True

            # Названия
            if data.get("full_name") and data["full_name"] != org.full_name:
                org.full_name = data["full_name"]
                updated = True

            if data.get("short_name") and data["short_name"] != org.short_name:
                org.short_name = data["short_name"]
                updated = True

            if (
                data.get("full_name_without_opf")
                and data["full_name_without_opf"] != org.full_name_without_opf
            ):
                org.full_name_without_opf = data["full_name_without_opf"]
                updated = True

            if (
                data.get("short_name_without_opf")
                and data["short_name_without_opf"] != org.short_name_without_opf
            ):
                org.short_name_without_opf = data["short_name_without_opf"]
                updated = True

            if data.get("latin_name") and data["latin_name"] != org.latin_name:
                org.latin_name = data["latin_name"]
                updated = True

            # ФИО для ИП
            if data.get("fio_surname") and data["fio_surname"] != org.fio_surname:
                org.fio_surname = data["fio_surname"]
                updated = True

            if data.get("fio_name") and data["fio_name"] != org.fio_name:
                org.fio_name = data["fio_name"]
                updated = True

            if (
                data.get("fio_patronymic")
                and data["fio_patronymic"] != org.fio_patronymic
            ):
                org.fio_patronymic = data["fio_patronymic"]
                updated = True

            # ОПФ
            if data.get("opf_code") and data["opf_code"] != org.opf_code:
                org.opf_code = data["opf_code"]
                updated = True

            if data.get("opf_full") and data["opf_full"] != org.opf_full:
                org.opf_full = data["opf_full"]
                updated = True

            if data.get("opf_short") and data["opf_short"] != org.opf_short:
                org.opf_short = data["opf_short"]
                updated = True

            if data.get("opf_type") and data["opf_type"] != org.opf_type:
                org.opf_type = data["opf_type"]
                updated = True

            # Адрес
            if data.get("address_raw") and data["address_raw"] != org.address_raw:
                org.address_raw = data["address_raw"]
                updated = True

            if (
                data.get("address_source")
                and data["address_source"] != org.address_source
            ):
                org.address_source = data["address_source"]
                updated = True

            if data.get("address_qc") and data["address_qc"] != org.address_qc:
                org.address_qc = data["address_qc"]
                updated = True

            if data.get("postal_code") and data["postal_code"] != org.postal_code:
                org.postal_code = data["postal_code"]
                updated = True

            if data.get("region") and data["region"] != org.region:
                org.region = data["region"]
                updated = True

            if data.get("city") and data["city"] != org.city:
                org.city = data["city"]
                updated = True

            if data.get("street") and data["street"] != org.street:
                org.street = data["street"]
                updated = True

            if data.get("house") and data["house"] != org.house:
                org.house = data["house"]
                updated = True

            # Координаты
            if data.get("coordinates") and data["coordinates"] != org.coordinates:
                org.coordinates = data["coordinates"]
                updated = True

            # Статус и состояние
            if data.get("status") and data["status"] != org.status:
                org.status = data["status"]
                updated = True

            if data.get("status_code") and data["status_code"] != org.status_code:
                org.status_code = data["status_code"]
                updated = True

            if (
                data.get("actuality_date")
                and data["actuality_date"] != org.actuality_date
            ):
                if isinstance(data["actuality_date"], date):
                    org.actuality_date = data["actuality_date"]
                    updated = True
                elif isinstance(data["actuality_date"], str):
                    from datetime import datetime

                    try:
                        org.actuality_date = datetime.fromisoformat(
                            data["actuality_date"].replace("Z", "+00:00")
                        ).date()
                        updated = True
                    except (ValueError, TypeError):
                        pass

            # Коды статистики
            if data.get("okpo") and data["okpo"] != org.okpo:
                org.okpo = data["okpo"]
                updated = True

            if data.get("okato") and data["okato"] != org.okato:
                org.okato = data["okato"]
                updated = True

            if data.get("oktmo") and data["oktmo"] != org.oktmo:
                org.oktmo = data["oktmo"]
                updated = True

            if data.get("okogu") and data["okogu"] != org.okogu:
                org.okogu = data["okogu"]
                updated = True

            if data.get("okfs") and data["okfs"] != org.okfs:
                org.okfs = data["okfs"]
                updated = True

            if data.get("okved") and data["okved"] != org.okved:
                org.okved = data["okved"]
                updated = True

            if data.get("okved_type") and data["okved_type"] != org.okved_type:
                org.okved_type = data["okved_type"]
                updated = True

            # Руководство
            if data.get("manager_name") and data["manager_name"] != org.manager_name:
                org.manager_name = data["manager_name"]
                updated = True

            if data.get("manager_post") and data["manager_post"] != org.manager_post:
                org.manager_post = data["manager_post"]
                updated = True

            if (
                data.get("manager_start_date")
                and data["manager_start_date"] != org.manager_start_date
            ):
                if isinstance(data["manager_start_date"], date):
                    org.manager_start_date = data["manager_start_date"]
                    updated = True
                elif isinstance(data["manager_start_date"], str):
                    from datetime import datetime

                    try:
                        org.manager_start_date = datetime.fromisoformat(
                            data["manager_start_date"].replace("Z", "+00:00")
                        ).date()
                        updated = True
                    except (ValueError, TypeError):
                        pass

            # Филиалы
            if (
                data.get("branch_count") is not None
                and data["branch_count"] != org.branch_count
            ):
                org.branch_count = data["branch_count"]
                updated = True

            if data.get("branch_type") and data["branch_type"] != org.branch_type:
                org.branch_type = data["branch_type"]
                updated = True

            # Даты регистрации
            if (
                data.get("registration_date")
                and data["registration_date"] != org.registration_date
            ):
                if isinstance(data["registration_date"], date):
                    org.registration_date = data["registration_date"]
                    updated = True
                elif isinstance(data["registration_date"], str):
                    from datetime import datetime

                    try:
                        org.registration_date = datetime.fromisoformat(
                            data["registration_date"].replace("Z", "+00:00")
                        ).date()
                        updated = True
                    except (ValueError, TypeError):
                        pass

            if (
                data.get("liquidation_date")
                and data["liquidation_date"] != org.liquidation_date
            ):
                if isinstance(data["liquidation_date"], date):
                    org.liquidation_date = data["liquidation_date"]
                    updated = True
                elif isinstance(data["liquidation_date"], str):
                    from datetime import datetime

                    try:
                        org.liquidation_date = datetime.fromisoformat(
                            data["liquidation_date"].replace("Z", "+00:00")
                        ).date()
                        updated = True
                    except (ValueError, TypeError):
                        pass

            if updated:
                org.save()
                updated_count += 1

        if updated_count > 0:
            messages.success(
                request, f"Обновлено {updated_count} организаций из DaData"
            )
        if no_data_count > 0:
            messages.warning(
                request, f"Для {no_data_count} организаций не найдены данные в DaData"
            )
        if error_count > 0:
            messages.error(request, f"Ошибок: {error_count}")

    update_from_dadata.short_description = "Обновить выбранные организации из DaData"
