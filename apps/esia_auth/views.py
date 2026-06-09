from django.shortcuts import redirect
from django.contrib.auth import logout
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def esia_login(request):
    """
    Перенаправление на вход через ЕСИА
    Шлюз инициирует авторизацию и устанавливает cookie X1_SSO
    """
    # Получаем URL для редиректа после входа
    next_url = request.GET.get("next", "/")

    # Берем URL шлюза из настроек
    esia_gateway_url = settings.ESIA_GATEWAY_URL.rstrip("/")
    esia_gateway_auth_url = f"{esia_gateway_url}/auth/esia"

    # Формируем callback URL (куда шлюз вернет пользователя после авторизации)
    # redirect_uri - параметр для шлюза, чтобы он знал, куда вернуться
    callback_url = request.build_absolute_uri("/esia/callback/")

    # Сохраняем next_url в сессию, чтобы после callback вернуть пользователя куда нужно
    request.session["esia_next_url"] = next_url

    # Перенаправляем на шлюз
    return redirect(f"{esia_gateway_auth_url}?redirect_uri={callback_url}")


def esia_callback(request):
    """
    Callback после авторизации в ЕСИА
    Сюда шлюз возвращает пользователя после успешной авторизации
    Шлюз уже установил cookie X1_SSO
    """
    # Получаем сохраненный URL для редиректа
    next_url = request.session.pop("esia_next_url", "/")

    # Можно также проверить статус авторизации через параметр от шлюза
    error = request.GET.get("error")
    if error:
        logger.error(f"ESIA auth error: {error}")
        # Перенаправляем на страницу входа с ошибкой
        return redirect(f"{settings.LOGIN_URL}?error=esia_failed")

    return redirect(next_url)


def esia_logout(request):
    """Выход из системы"""
    # Получаем URL шлюза для выхода
    esia_gateway_url = settings.ESIA_GATEWAY_URL.rstrip("/")
    esia_gateway_logout_url = f"{esia_gateway_url}/auth/logout"

    # Выходим из Django
    logout(request)

    # Перенаправляем на шлюз для выхода из ЕСИА
    # Шлюз после выхода вернет пользователя на главную
    return redirect(esia_gateway_logout_url)
