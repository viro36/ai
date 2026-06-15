from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import CourseRecommendation, RecommendationTask
from .tasks import generate_recommendations_for_user
from .utils import (
    has_completed_all_surveys,
    has_completed_profile,
    is_ready_for_recommendations,
)


@login_required
def my_recommendations(request):
    """Отображает рекомендации пользователя"""
    recommendations = CourseRecommendation.objects.filter(
        user=request.user
    ).select_related("course")[:10]

    task_status = RecommendationTask.objects.filter(user=request.user).first()

    ready_for_recs = is_ready_for_recommendations(request.user)
    all_surveys_completed = has_completed_all_surveys(request.user)
    profile_completed = has_completed_profile(request.user)

    context = {
        "recommendations": recommendations,
        "task_status": task_status,
        "has_recommendations": recommendations.exists(),
        "ready_for_recommendations": ready_for_recs,
        "all_surveys_completed": all_surveys_completed,
        "profile_completed": profile_completed,
    }
    return render(request, "recommendations/my_recommendations.html", context)


@login_required
def generate_recommendations(request):
    """Запускает генерацию рекомендаций (без очистки старых)"""
    if request.method == "POST":
        if not is_ready_for_recommendations(request.user):
            messages.warning(
                request, "Пожалуйста, сначала пройдите все опросы и заполните анкету."
            )
            return redirect("surveys:survey_list")

        existing_task = RecommendationTask.objects.filter(
            user=request.user, status="pending"
        ).first()

        if existing_task:
            messages.warning(
                request, "Рекомендации уже генерируются. Пожалуйста, подождите."
            )
            return redirect("recommendations:my_recommendations")

        task = generate_recommendations_for_user.delay(request.user.id)

        RecommendationTask.objects.update_or_create(
            user=request.user,
            defaults={
                "task_id": task.id,
                "status": "pending",
                "error_message": None,
            },
        )

        messages.success(
            request,
            "Генерация рекомендаций запущена! Это может занять несколько минут.",
        )

    return redirect("recommendations:my_recommendations")


@login_required
def regenerate_recommendations(request):
    """Перегенерирует рекомендации (очищает старые и запускает заново)"""
    if request.method == "POST":
        if not is_ready_for_recommendations(request.user):
            messages.warning(
                request, "Пожалуйста, сначала пройдите все опросы и заполните анкету."
            )
            return redirect("surveys:survey_list")

        # Очищаем старые рекомендации
        CourseRecommendation.objects.filter(user=request.user).delete()

        # Удаляем старую задачу, если была
        RecommendationTask.objects.filter(user=request.user).delete()

        # Запускаем новую задачу
        task = generate_recommendations_for_user.delay(request.user.id)

        RecommendationTask.objects.create(
            user=request.user,
            task_id=task.id,
            status="pending",
        )

        messages.success(
            request,
            "Обновление рекомендаций запущено! Это может занять несколько минут.",
        )

    return redirect("recommendations:my_recommendations")


@login_required
def check_recommendations_status(request):
    """AJAX проверка статуса генерации"""
    task_status = RecommendationTask.objects.filter(user=request.user).first()

    if task_status and task_status.status == "completed":
        recommendations_count = CourseRecommendation.objects.filter(
            user=request.user
        ).count()
        return JsonResponse(
            {
                "status": "completed",
                "has_recommendations": recommendations_count > 0,
                "count": recommendations_count,
            }
        )
    elif task_status and task_status.status == "failed":
        return JsonResponse(
            {
                "status": "failed",
                "error": task_status.error_message,
            }
        )
    else:
        return JsonResponse({"status": "pending"})
