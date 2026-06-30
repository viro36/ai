from apps.surveys.models import SurveyCategory


def get_all_survey_categories():
    """Возвращает список названий категорий опросов"""
    return list(
        SurveyCategory.objects.filter(is_active=True).values_list("name", flat=True)
    )


def has_completed_all_surveys(user):
    """Проверяет, прошёл ли пользователь все активные опросы (НЕОБЯЗАТЕЛЬНО)"""
    required_categories = SurveyCategory.objects.filter(is_active=True)
    completed_count = 0
    total_count = required_categories.count()

    for category in required_categories:
        has_completed = user.survey_sessions.filter(
            category=category, status="completed"
        ).exists()
        if has_completed:
            completed_count += 1

    return {
        "completed": completed_count,
        "total": total_count,
        "all_completed": completed_count == total_count and total_count > 0,
    }


def has_completed_profile(user):
    """Проверяет, заполнена ли анкета пользователя (ОБЯЗАТЕЛЬНО)"""
    if not hasattr(user, "employee_profile"):
        return False

    profile = user.employee_profile

    # Проверяем поля пользователя
    if not user.last_name:
        return False
    if not user.first_name:
        return False

    # Проверяем поля профиля
    required_profile_fields = [
        "snils",
        "organization",
        "position",
        "position_level",
        "education_level",
        "graduation_year",
        "education_institution",
        "specialty",
        "locality",
        "municipality",
    ]

    for field in required_profile_fields:
        value = getattr(profile, field)
        if not value:
            return False

    return True


def is_ready_for_recommendations(user):
    """Проверяет, готов ли пользователь к получению рекомендаций (только анкета обязательна)"""
    profile_completed = has_completed_profile(user)
    return profile_completed
