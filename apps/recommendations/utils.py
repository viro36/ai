from apps.surveys.models import SurveyCategory


def get_all_survey_categories():
    """Возвращает список названий категорий опросов"""
    return list(
        SurveyCategory.objects.filter(is_active=True).values_list("name", flat=True)
    )


def has_completed_all_surveys(user):
    """Проверяет, прошёл ли пользователь все активные опросы"""
    required_categories = SurveyCategory.objects.filter(is_active=True)

    for category in required_categories:
        has_completed = user.survey_sessions.filter(
            category=category, status="completed"
        ).exists()
        if not has_completed:
            print(f"  -> MISSING: {category.name}")
            return False

    return True


def has_completed_profile(user):
    """Проверяет, заполнена ли анкета пользователя"""
    # Проверяем, что у пользователя есть профиль работника
    if not hasattr(user, "employee_profile"):
        print(f"  No employee_profile")
        return False

    profile = user.employee_profile

    # Обязательные поля для заполнения
    required_fields = ["position", "position_level"]

    for field in required_fields:
        value = getattr(profile, field)
        if not value:
            return False

    return True


def is_ready_for_recommendations(user):
    """Проверяет, готов ли пользователь к получению рекомендаций"""
    all_surveys = has_completed_all_surveys(user)
    profile = has_completed_profile(user)
    result = all_surveys and profile

    return result
