from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.courses.models import Course
from .services import DeepSeekRecommendationService
from .models import CourseRecommendation, RecommendationTask
from .utils import has_completed_profile

User = get_user_model()


@shared_task(bind=True)
def generate_recommendations_for_user(self, user_id, session_id=None):
    """Генерирует рекомендации для пользователя на основе профиля и опросов (если есть)"""
    try:
        user = User.objects.get(id=user_id)

        if not has_completed_profile(user):
            raise ValueError("Пользователь не заполнил анкету")

        service = DeepSeekRecommendationService(user)
        recommendations = service.get_recommendations()

        CourseRecommendation.objects.filter(user=user).delete()

        created_count = 0
        for idx, rec in enumerate(recommendations):
            course_id = rec.get("course_id")
            if not course_id:
                continue

            try:
                course = Course.objects.get(id=course_id, is_deleted=False)
                # AI возвращает 0-100, сохраняем как есть (в модели поле FloatField, хранит 0-1)
                # Поэтому делим на 100
                relevance_score = rec.get("relevance_score", 0)
                # Проверяем, если значение > 1, значит это 0-100, делим на 100
                if relevance_score > 1:
                    relevance_score = relevance_score / 100
                elif relevance_score < 0:
                    relevance_score = 0.0

                CourseRecommendation.objects.create(
                    user=user,
                    session_id=session_id,
                    course=course,
                    reason=rec.get("reason", ""),
                    relevance_score=relevance_score,
                    order=idx,
                )
                created_count += 1
            except Course.DoesNotExist:
                continue

        task_id = getattr(self.request, "id", None)

        RecommendationTask.objects.update_or_create(
            user=user,
            defaults={
                "task_id": task_id or f"manual-{user_id}-{timezone.now().timestamp()}",
                "status": "completed",
                "error_message": None,
            },
        )

        return {"status": "success", "created": created_count}

    except User.DoesNotExist:
        return {"status": "error", "error": "User not found"}

    except Exception as e:
        try:
            task_id = getattr(self.request, "id", None)
            RecommendationTask.objects.update_or_create(
                user=user,
                defaults={
                    "task_id": task_id
                    or f"manual-{user_id}-{timezone.now().timestamp()}",
                    "status": "failed",
                    "error_message": str(e),
                },
            )
        except UnboundLocalError:
            return {"status": "error", "error": str(e)}

        return {"status": "error", "error": str(e)}


@shared_task
def generate_recommendations_for_all_employees():
    """Генерирует рекомендации для всех работников, у кого заполнена анкета"""
    users = (
        User.objects.filter(user_type="employee", is_active=True)
        .exclude(employee_profile__isnull=True)
        .exclude(employee_profile__position__isnull=True, employee_profile__position="")
    )

    for user in users:
        generate_recommendations_for_user.delay(user.id)
