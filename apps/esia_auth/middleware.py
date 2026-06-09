import logging
from django.utils.deprecation import MiddlewareMixin
from .services import EsiaGatewayService
from .auth import login_or_create_user

logger = logging.getLogger(__name__)


class EsiaAuthMiddleware(MiddlewareMixin):
    """
    Middleware для автоматической авторизации через ЕСИА
    """

    # Добавляем async_mode для совместимости с Django 6.0
    async_mode = False

    def __init__(self, get_response):
        self.get_response = get_response
        self.esia_service = EsiaGatewayService()

    def __call__(self, request):
        # Пропускаем определенные пути
        excluded_paths = [
            "/admin/",
            "/static/",
            "/media/",
            "/accounts/login/",
            "/accounts/logout/",
            "/esia/login/",
            "/esia/callback/",
            "/esia/logout/",
        ]

        if any(request.path.startswith(path) for path in excluded_paths):
            return self.get_response(request)

        # Получаем X1_SSO из cookie
        session_id = request.COOKIES.get("X1_SSO")

        if not session_id:
            return self.get_response(request)

        # Если пользователь уже авторизован
        if request.user.is_authenticated:
            # Проверяем, нужно ли обновить данные
            if request.user.esia_verified:
                return self.get_response(request)

            # Синхронно получаем данные (без asyncio.run)
            import httpx

            try:
                with httpx.Client(timeout=self.esia_service.timeout) as client:
                    response = client.get(
                        f"{self.esia_service.gateway_url}/session/get",
                        params={"sid": session_id, "appkey": self.esia_service.app_key},
                    )
                    response.raise_for_status()
                    data = response.json()

                    if data:
                        from .auth import _update_user_from_esia

                        _update_user_from_esia(request.user, data, self.esia_service)
            except Exception as e:
                logger.error(f"Error updating user data: {e}")

            return self.get_response(request)

        # Авторизуем пользователя
        try:
            import httpx

            with httpx.Client(timeout=self.esia_service.timeout) as client:
                response = client.get(
                    f"{self.esia_service.gateway_url}/session/get",
                    params={"sid": session_id, "appkey": self.esia_service.app_key},
                )
                response.raise_for_status()
                data = response.json()

                if data:
                    user = login_or_create_user(data, self.esia_service)
                    if user:
                        from django.contrib.auth import login

                        login(request, user)
                        logger.info(f"User {user.username} logged in via ESIA")
        except Exception as e:
            logger.error(f"Error in ESIA middleware: {e}")

        return self.get_response(request)

    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response
