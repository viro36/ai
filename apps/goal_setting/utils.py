from .models import Question, GoalSettingResponse


def has_completed_goal_setting(user):
    """
    Проверяет, заполнено ли целеполагание пользователем.
    Возвращает False, если нет активных вопросов.
    """
    questions = Question.objects.filter(is_active=True)
    total = questions.count()

    # Если нет активных вопросов, целеполагание не может быть заполнено
    if total == 0:
        return False

    answered = GoalSettingResponse.objects.filter(user=user).count()
    return answered == total


def get_goal_setting_progress(user):
    """Возвращает прогресс заполнения целеполагания"""
    questions = Question.objects.filter(is_active=True)
    total = questions.count()
    answered = GoalSettingResponse.objects.filter(user=user).count()

    if total == 0:
        return {"total": 0, "answered": 0, "progress": 0, "is_complete": False}

    return {
        "total": total,
        "answered": answered,
        "progress": int(answered / total * 100),
        "is_complete": answered == total,
    }
