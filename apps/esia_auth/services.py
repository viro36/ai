# apps/esia_auth/services.py
import httpx
import logging
from django.conf import settings
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EsiaGatewayService:
    """Сервис для взаимодействия со шлюзом ЕСИА"""

    def __init__(self):
        self.gateway_url = getattr(
            settings, "ESIA_GATEWAY_URL", "http://localhost:8080"
        )
        self.app_key = getattr(settings, "ESIA_APP_KEY", "")
        self.timeout = getattr(settings, "ESIA_TIMEOUT", 10)

    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """
        Получить данные пользователя из шлюза по session_id (X1_SSO)
        Синхронная версия
        """
        if not session_id:
            logger.warning("Empty session_id provided")
            return None

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.gateway_url}/session/get",
                    params={"sid": session_id, "appkey": self.app_key},
                )
                response.raise_for_status()
                data = response.json()

                # Проверяем, что пришли ожидаемые поля
                if not data.get("login") and not data.get("email"):
                    logger.error(f"Invalid ESIA response: missing required fields")
                    return None

                return data

        except httpx.TimeoutException:
            logger.error(f"ESIA gateway timeout for session {session_id}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"ESIA gateway HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"ESIA gateway error: {str(e)}")
            return None

    def validate_snils(self, snils: str) -> bool:
        """Валидация СНИЛС"""
        snils = "".join(filter(str.isdigit, snils))

        if len(snils) != 11:
            return False

        # Расчет контрольной суммы
        sum_ = 0
        for i in range(9):
            sum_ += int(snils[i]) * (9 - i)

        check_digit = 0
        if sum_ < 100:
            check_digit = sum_
        elif sum_ > 101:
            check_digit = sum_ % 101
            if check_digit == 100:
                check_digit = 0

        return check_digit == int(snils[-2:])

    def format_fio(self, value: str) -> str:
        """Форматирование ФИО (первая буква заглавная, остальные строчные)"""
        if not value:
            return ""
        return value.lower().title()
