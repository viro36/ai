import logging
from dadata import Dadata
from django.conf import settings

logger = logging.getLogger(__name__)


def get_organization_by_inn(inn: str, debug=False):
    """
    Получает данные об организации по ИНН через API DaData.
    """
    token = settings.DADATA_API_KEY

    if not token:
        logger.error("DADATA_API_KEY не настроен")
        return None

    try:
        with Dadata(token) as dadata:
            result = dadata.find_by_id(name="party", query=inn, count=1)

            if result:
                return parse_dadata_response(result[0])
            else:
                logger.warning(f"Организация с ИНН {inn} не найдена в DaData")
                return None

    except Exception as e:
        logger.error(f"Ошибка при запросе к DaData: {e}")
        return None


def parse_dadata_response(data: dict):
    """Преобразует ответ DaData в удобный словарь со всеми полями."""
    from datetime import datetime, timezone

    org_data = data.get("data", {})
    address_data = org_data.get("address", {}).get("data", {})
    opf_data = org_data.get("opf", {})
    fio_data = org_data.get("fio", {})
    state_data = org_data.get("state", {})
    management_data = org_data.get("management", {})

    # Координаты
    coordinates = None
    geo_lat = address_data.get("geo_lat")
    geo_lon = address_data.get("geo_lon")
    if geo_lat and geo_lon:
        coordinates = f"{geo_lat}, {geo_lon}"

    # Статус
    status_map = {
        "ACTIVE": "ACTIVE",
        "LIQUIDATING": "LIQUIDATING",
        "LIQUIDATED": "LIQUIDATED",
        "REORGANIZING": "REORGANIZING",
        "BANKRUPT": "BANKRUPT",
    }
    status = status_map.get(state_data.get("status"), state_data.get("status"))

    # Обработка дат (из миллисекунд или ISO строки)
    def parse_date(date_value):
        if not date_value:
            return None
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, (int, float)):
            # Это миллисекунды с 1970 года
            try:
                return datetime.fromtimestamp(date_value / 1000, tz=timezone.utc).date()
            except (ValueError, OSError):
                return None
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                return None
        return None

    return {
        # Основные реквизиты
        "inn": org_data.get("inn"),
        "kpp": org_data.get("kpp"),
        "kpp_largest": org_data.get("kpp_largest"),
        "ogrn": org_data.get("ogrn"),
        "ogrn_date": parse_date(org_data.get("ogrn_date")),
        "hid": org_data.get("hid"),
        "org_type": org_data.get("type"),
        # Наименования
        "full_name": org_data.get("name", {}).get("full_with_opf"),
        "short_name": org_data.get("name", {}).get("short_with_opf"),
        "full_name_without_opf": org_data.get("name", {}).get("full"),
        "short_name_without_opf": org_data.get("name", {}).get("short"),
        "latin_name": org_data.get("name", {}).get("latin"),
        # ФИО для ИП
        "fio_surname": fio_data.get("surname"),
        "fio_name": fio_data.get("name"),
        "fio_patronymic": fio_data.get("patronymic"),
        # ОПФ
        "opf_code": opf_data.get("code"),
        "opf_full": opf_data.get("full"),
        "opf_short": opf_data.get("short"),
        "opf_type": opf_data.get("type"),
        # Адрес
        "address_raw": org_data.get("address", {}).get("unrestricted_value"),
        "address_source": address_data.get("source"),
        "address_qc": address_data.get("qc"),
        "postal_code": address_data.get("postal_code"),
        "region": address_data.get("region_with_type"),
        "city": address_data.get("city_with_type"),
        "street": address_data.get("street_with_type"),
        "house": address_data.get("house"),
        # Координаты
        "coordinates": coordinates,
        # Статус и состояние
        "status": status,
        "status_code": state_data.get("code"),
        "actuality_date": parse_date(state_data.get("actuality_date")),
        "registration_date": parse_date(state_data.get("registration_date")),
        "liquidation_date": parse_date(state_data.get("liquidation_date")),
        # Коды статистики
        "okpo": org_data.get("okpo"),
        "okato": org_data.get("okato"),
        "oktmo": org_data.get("oktmo"),
        "okogu": org_data.get("okogu"),
        "okfs": org_data.get("okfs"),
        "okved": org_data.get("okved"),
        "okved_type": org_data.get("okved_type"),
        # Руководство
        "manager_name": management_data.get("name"),
        "manager_post": management_data.get("post"),
        "manager_start_date": parse_date(management_data.get("start_date")),
        # Филиалы
        "branch_count": org_data.get("branch_count"),
        "branch_type": org_data.get("branch_type"),
    }
