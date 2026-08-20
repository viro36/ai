from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone

from apps.accounts.models import EmployeeProfile
from apps.users.models import CustomUser

from .models import (
    ApprovedSelectedCourse,
    CourseRecommendation,
    EmployerRecommendation,
    RecommendationTask,
    SelectedCourse,
)
from .tasks import generate_recommendations_for_user
from .utils import (
    has_completed_all_surveys,
    has_completed_profile,
    is_ready_for_recommendations,
)
from apps.courses.models import Category, Course


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

        next_url = request.POST.get("next", "")
        if next_url:
            return redirect(next_url)
        return redirect("recommendations:my_recommendations")
    return redirect("recommendations:my_recommendations")


@login_required
def selected_courses(request):
    """Список выбранных курсов пользователя"""
    selected = (
        SelectedCourse.objects.filter(user=request.user)
        .select_related("course", "course__organization")
        .prefetch_related("approval")
    )

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


@login_required
def approve_selected_course(request, selected_course_id):
    """Одобрение/отклонение выбранного курса работодателем"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    selected = get_object_or_404(SelectedCourse, id=selected_course_id)

    # Проверяем, что работодатель имеет доступ к этому сотруднику
    if request.user.user_type == "employer":
        if selected.user.organization != request.user.organization:
            messages.error(request, "У вас нет доступа к этому сотруднику")
            return redirect("accounts:employee_list")

    if request.method == "POST":
        action = request.POST.get("action")
        comment = request.POST.get("comment", "")

        if action in ["approve", "reject"]:
            approval, created = ApprovedSelectedCourse.objects.get_or_create(
                selected_course=selected,
                defaults={
                    "status": "approved" if action == "approve" else "rejected",
                    "approved_by": request.user,
                    "approved_at": timezone.now(),
                    "comment": comment,
                },
            )
            if not created:
                approval.status = "approved" if action == "approve" else "rejected"
                approval.approved_by = request.user
                approval.approved_at = timezone.now()
                if comment:
                    approval.comment = comment
                approval.save()

            status_text = "одобрен" if action == "approve" else "отклонён"
            messages.success(
                request,
                f'Курс "{selected.course.title}" {status_text} для сотрудника {selected.user.get_full_name()}',
            )
        else:
            messages.error(request, "Неверное действие")

    return redirect("accounts:employee_selected_courses", employee_id=selected.user.id)


@login_required
def employer_recommendations(request):
    """Страница рекомендаций курсов работодателем"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    organization = request.user.organization

    # Получаем все категории
    categories = Category.objects.all().order_by("name")

    # Получаем все должности работников организации (из анкеты)
    positions = (
        EmployeeProfile.objects.filter(
            user__organization=organization,
            user__user_type="employee",
            user__is_active=True,
        )
        .exclude(position__isnull=True)
        .exclude(position="")
        .values_list("position", flat=True)
        .distinct()
        .order_by("position")
    )

    # Получаем всех сотрудников с количеством рекомендаций
    employees = (
        CustomUser.objects.filter(
            organization=organization, user_type="employee", is_active=True
        )
        .annotate(
            recommendations_count=Count(
                "employee_recommendations",
                filter=Q(employee_recommendations__employer=request.user),
            )
        )
        .select_related("employee_profile")
        .order_by("last_name", "first_name")
    )

    context = {
        "categories": categories,
        "positions": positions,
        "employees": employees,
    }
    return render(request, "recommendations/employer_recommendations.html", context)


@login_required
def get_employees_by_position(request):
    """AJAX получение списка работников по должности"""
    if request.user.user_type not in ["employer", "admin"]:
        return JsonResponse({"error": "Доступ запрещён"}, status=403)

    position = request.GET.get("position")
    organization = request.user.organization

    employees = CustomUser.objects.filter(
        organization=organization,
        user_type="employee",
        is_active=True,
        employee_profile__position=position,
    ).values("id", "last_name", "first_name", "patronymic")

    return JsonResponse({"employees": list(employees)})


@login_required
def get_courses_by_category(request):
    """AJAX получение списка курсов по категории"""
    if request.user.user_type not in ["employer", "admin"]:
        return JsonResponse({"error": "Доступ запрещён"}, status=403)

    category_id = request.GET.get("category_id")
    organization = request.user.organization

    courses = Course.objects.filter(
        categories__id=category_id, is_deleted=False
    ).values("id", "title", "organization__short_name")

    return JsonResponse({"courses": list(courses)})


@login_required
def send_employer_recommendation(request):
    """Отправка рекомендации курса работнику"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        course_id = request.POST.get("course_id")
        reason = request.POST.get("reason", "")

        employee = get_object_or_404(CustomUser, id=employee_id, user_type="employee")
        course = get_object_or_404(Course, id=course_id, is_deleted=False)

        # Проверяем, что сотрудник belongs к организации работодателя
        if employee.organization != request.user.organization:
            messages.error(request, "Этот сотрудник не принадлежит вашей организации")
            return redirect("recommendations:employer_recommendations")

        # Создаём или обновляем рекомендацию
        recommendation, created = EmployerRecommendation.objects.update_or_create(
            employer=request.user,
            employee=employee,
            course=course,
            defaults={
                "reason": reason,
                "is_viewed": False,
            },
        )

        if created:
            messages.success(
                request,
                f'Курс "{course.title}" рекомендован сотруднику {employee.get_full_name()}',
            )
        else:
            messages.info(
                request,
                f'Рекомендация курса "{course.title}" для {employee.get_full_name()} обновлена',
            )

        return redirect("recommendations:employer_recommendations")

    return redirect("recommendations:employer_recommendations")


@login_required
def employee_employer_recommendations(request):
    """Список рекомендаций от работодателя для работника"""
    if request.user.user_type != "employee":
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    recommendations = (
        EmployerRecommendation.objects.filter(employee=request.user)
        .select_related("employer", "course", "course__organization")
        .order_by("-created_at")
    )

    # Отмечаем как просмотренные
    recommendations.filter(is_viewed=False).update(is_viewed=True)

    # Получаем ID выбранных курсов пользователя (как в my_recommendations)
    selected_course_ids = list(
        SelectedCourse.objects.filter(user=request.user).values_list(
            "course_id", flat=True
        )
    )

    context = {
        "recommendations": recommendations,
        "total": recommendations.count(),
        "selected_course_ids": selected_course_ids,
    }
    return render(
        request, "recommendations/employee_employer_recommendations.html", context
    )


@login_required
def remove_employer_recommendation(request, pk):
    """Удаление рекомендации работодателя"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    recommendation = get_object_or_404(
        EmployerRecommendation, pk=pk, employer=request.user
    )

    if request.method == "POST":
        recommendation.delete()
        messages.success(request, "Рекомендация удалена")

    return redirect("recommendations:employer_recommendations")


@login_required
def employee_recommendations_detail(request, employee_id):
    """Детальный просмотр рекомендаций для конкретного сотрудника"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    employee = get_object_or_404(
        CustomUser,
        id=employee_id,
        organization=request.user.organization,
        user_type="employee",
        is_active=True,
    )

    recommendations = (
        EmployerRecommendation.objects.filter(employer=request.user, employee=employee)
        .select_related("course", "course__organization")
        .order_by("-created_at")
    )

    context = {
        "employee": employee,
        "recommendations": recommendations,
        "total": recommendations.count(),
    }
    return render(
        request, "recommendations/employee_recommendations_detail.html", context
    )
