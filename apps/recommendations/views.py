from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import CourseRecommendation, RecommendationTask, SelectedCourse
from .tasks import generate_recommendations_for_user
from .utils import (
    has_completed_all_surveys,
    has_completed_profile,
    is_ready_for_recommendations,
)
from apps.courses.models import Course


@login_required
def my_recommendations(request):
    """Отображает рекомендации пользователя с пагинацией"""
    recommendations_list = CourseRecommendation.objects.filter(
        user=request.user
    ).select_related("course")

    # Пагинация по 20 рекомендаций на страницу
    paginator = Paginator(recommendations_list, 20)
    page_number = request.GET.get("page", 1)
    recommendations = paginator.get_page(page_number)

    task_status = RecommendationTask.objects.filter(user=request.user).first()

    ready_for_recs = is_ready_for_recommendations(request.user)
    profile_completed = has_completed_profile(request.user)
    surveys_info = has_completed_all_surveys(request.user)

    # Получаем ID выбранных курсов (как числа)
    selected_course_ids = list(
        SelectedCourse.objects.filter(user=request.user).values_list(
            "course_id", flat=True
        )
    )

    context = {
        "recommendations": recommendations,
        "task_status": task_status,
        "has_recommendations": recommendations_list.exists(),
        "ready_for_recommendations": ready_for_recs,
        "profile_completed": profile_completed,
        "surveys_completed": surveys_info["completed"],
        "surveys_total": surveys_info["total"],
        "all_surveys_completed": surveys_info["all_completed"],
        "has_surveys": surveys_info["total"] > 0,
        "paginator": paginator,
        "page_obj": recommendations,
        "selected_course_ids": selected_course_ids,
    }
    return render(request, "recommendations/my_recommendations.html", context)


@login_required
def generate_recommendations(request):
    """Запускает генерацию рекомендаций (без очистки старых)"""
    if request.method == "POST":
        if not is_ready_for_recommendations(request.user):
            messages.warning(request, "Пожалуйста, сначала заполните анкету.")
            return redirect("accounts:employee_profile")

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
            messages.warning(request, "Пожалуйста, сначала заполните анкету.")
            return redirect("accounts:employee_profile")

        CourseRecommendation.objects.filter(user=request.user).delete()
        RecommendationTask.objects.filter(user=request.user).delete()

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


@login_required
def select_course(request, course_id):
    """Выбор курса пользователем"""
    if request.method == "POST":
        course = get_object_or_404(Course, id=course_id, is_deleted=False)

        if SelectedCourse.objects.filter(user=request.user, course=course).exists():
            messages.info(request, f'Курс "{course.title}" уже был выбран ранее.')
        else:
            SelectedCourse.objects.create(user=request.user, course=course)
            messages.success(request, f'Курс "{course.title}" успешно выбран!')

        return redirect("recommendations:my_recommendations")
    return redirect("recommendations:my_recommendations")


@login_required
def selected_courses(request):
    """Список выбранных курсов пользователя"""
    selected = SelectedCourse.objects.filter(user=request.user).select_related("course")

    context = {
        "selected_courses": selected,
        "total": selected.count(),
    }
    return render(request, "recommendations/selected_courses.html", context)


@login_required
def remove_selected_course(request, course_id):
    """Удаление выбранного курса"""
    if request.method == "POST":
        course = get_object_or_404(Course, id=course_id)
        SelectedCourse.objects.filter(user=request.user, course=course).delete()
        messages.success(request, f'Курс "{course.title}" удалён из выбранных.')
    return redirect("recommendations:selected_courses")
