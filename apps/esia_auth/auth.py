# apps/esia_auth/auth.py
import logging
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import datetime

User = get_user_model()
logger = logging.getLogger(__name__)


def login_or_create_user(esia_data: dict, esia_service):
    """
    Авторизация или создание пользователя на основе данных из ЕСИА
    """

    # 1. Поиск по СНИЛС
    snils = esia_data.get("login")
    if snils and esia_service.validate_snils(snils):
        try:
            user = User.objects.get(snils=snils)
            logger.info(f"User found by SNILS: {user.username}")
            return _update_user_from_esia(user, esia_data, esia_service)
        except User.DoesNotExist:
            pass
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple users with SNILS {snils}")

    # 2. Поиск по email (если есть)
    email = esia_data.get("email")
    if email:
        try:
            user = User.objects.get(email=email)
            logger.info(f"User found by email: {user.username}")
            return _update_user_from_esia(user, esia_data, esia_service)
        except User.DoesNotExist:
            pass

    # 3. Создание нового пользователя
    return _create_user_from_esia(esia_data, esia_service)


def _update_user_from_esia(user, esia_data, esia_service):
    """Обновление данных пользователя из ЕСИА"""

    # Обновляем основные поля
    user.first_name = esia_service.format_fio(esia_data.get("firstname", ""))
    user.last_name = esia_service.format_fio(esia_data.get("secondname", ""))

    if hasattr(user, "patronymic"):
        user.patronymic = esia_service.format_fio(esia_data.get("middlename", ""))

    if esia_data.get("email"):
        user.email = esia_data["email"]

    if esia_data.get("birthday"):
        user.birthday = datetime.fromisoformat(esia_data["birthday"])

    # Сохраняем СНИЛС если есть
    snils = esia_data.get("login")
    if snils and esia_service.validate_snils(snils):
        existing = User.objects.filter(snils=snils).exclude(id=user.id).first()
        if existing:
            logger.error(f"SNILS {snils} already linked to user {existing.id}")
        else:
            user.snils = snils

    # Устанавливаем тип пользователя
    if hasattr(user, "user_type"):
        user.user_type = User.UserType.ESIA

    if hasattr(user, "esia_id"):
        user.esia_id = snils or esia_data.get("login")
    if hasattr(user, "esia_verified"):
        user.esia_verified = True

    user.save()
    return user


def _create_user_from_esia(esia_data, esia_service):
    """Создание нового пользователя из данных ЕСИА"""

    # Генерируем логин и пароль
    username = get_random_string(30)
    password = get_random_string(12)

    # Создаем пользователя
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=esia_service.format_fio(esia_data.get("firstname", "")),
        last_name=esia_service.format_fio(esia_data.get("secondname", "")),
        email=esia_data.get("email"),
        is_active=True,
    )

    # Добавляем дополнительные поля
    if hasattr(user, "patronymic"):
        user.patronymic = esia_service.format_fio(esia_data.get("middlename", ""))

    if esia_data.get("birthday"):
        user.birthday = datetime.fromisoformat(esia_data["birthday"])

    # Сохраняем СНИЛС
    snils = esia_data.get("login")
    if snils and esia_service.validate_snils(snils):
        user.snils = snils

    # Устанавливаем тип пользователя
    if hasattr(user, "user_type"):
        user.user_type = User.UserType.ESIA

    if hasattr(user, "esia_id"):
        user.esia_id = snils or esia_data.get("login")
    if hasattr(user, "esia_verified"):
        user.esia_verified = True

    user.save()

    # Отправка email с паролем (если есть email)
    if user.email:
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            send_mail(
                subject="Регистрация на портале",
                message=f"Вы были зарегистрированы через Госуслуги.\n\n"
                f"Ваш логин: {username}\n"
                f"Пароль: {password}\n\n"
                f"Рекомендуем сменить пароль после входа.\n"
                f"В дальнейшем вы можете использовать этот логин и пароль "
                f"для входа без Госуслуг.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

    logger.info(f"Created new user {user.id} from ESIA")
    return user
