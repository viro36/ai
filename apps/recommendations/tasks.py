from celery import shared_task
from django.contrib.auth import get_user_model

from apps.courses.models import Course
from .services import DeepSeekRecommendationService
from .models import CourseRecommendation, RecommendationTask
from .utils import has_completed_all_surveys

User = get_user_model()


@shared_task(bind=True)
def generate_recommendations_for_user(self, user_id, session_id=None):
    """Генерирует рекомендации для пользователя на основе последних результатов опросов"""
    try:
        user = User.objects.get(id=user_id)

        if not has_completed_all_surveys(user):
            raise ValueError("Пользователь не прошёл все опросы")

        # Используем сервис, который автоматически берёт последние попытки
        service = DeepSeekRecommendationService(user)

        # Получаем рекомендации от AI (уже на основе последних данных)
        recommendations = service.get_recommendations()

        # Очищаем старые рекомендации
        CourseRecommendation.objects.filter(user=user).delete()

        # Сохраняем новые рекомендации
        for idx, rec in enumerate(recommendations):
            course_id = rec.get("course_id")
            if not course_id:
                continue

            try:
                course = Course.objects.get(id=course_id, is_deleted=False)
                CourseRecommendation.objects.create(
                    user=user,
                    session_id=session_id,
                    course=course,
                    reason=rec.get("reason", ""),
                    relevance_score=rec.get("relevance_score", 0.5),
                    order=idx,
                )
            except Course.DoesNotExist:
                continue

        # Обновляем статус задачи
        RecommendationTask.objects.update_or_create(
            user=user,
            defaults={
                "task_id": self.request.id,
                "status": "completed",
                "error_message": None,
            },
        )

        return {"status": "success", "count": len(recommendations)}

    except Exception as e:
        RecommendationTask.objects.update_or_create(
            user=user,
            defaults={
                "task_id": self.request.id,
                "status": "failed",
                "error_message": str(e),
            },
        )
        raise


@shared_task
def generate_recommendations_for_all_employees():
    """Генерирует рекомендации для всех работников, прошедших опросы"""
    users = User.objects.filter(
        user_type="employee", survey_sessions__status="completed", is_active=True
    ).distinct()

    for user in users:
        generate_recommendations_for_user.delay(user.id)
