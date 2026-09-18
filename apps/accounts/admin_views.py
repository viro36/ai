from django.contrib.admin import site as admin_site
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from apps.goal_setting.models import GoalSettingResponse, Question
from apps.organizations.models import Organization
from apps.recommendations.models import CourseRecommendation, SelectedCourse
from apps.surveys.models import RiasacResult, SurveyCategory, SurveySession
from .models import EmployeeProfile, EmployerRegistrationRequest

User = get_user_model()


def process_approve(registration):
    """
    Вспомогательная функция для одобрения заявки (без request)
    Возвращает созданных пользователя и организацию
    """
    # Проверяем, не существует ли уже организация с таким ИНН
    if Organization.objects.filter(inn=registration.inn).exists():
        organization = Organization.objects.get(inn=registration.inn)
    else:
        # Создаём организацию
        organization = Organization.objects.create(
            inn=registration.inn,
            full_name=registration.full_name,
            short_name=registration.short_name,
            address_raw="",
        )

    # Создаём пользователя
    user = User.objects.create_user(
        username=registration.username,
        email=registration.email,
        password=registration.password,
    )

    # Связываем пользователя с организацией
    user.organization = organization
    user.user_type = "employer"
    user.save()

    registration.status = "approved"
    registration.created_user = user
    registration.created_organization = organization
    registration.save()

    return user, organization


@staff_member_required
def approve_employer_request(request, request_id):
    """Одобрение заявки работодателя"""
    registration = get_object_or_404(
        EmployerRegistrationRequest, id=request_id, status="pending"
    )

    try:
        # Проверяем, не существует ли уже организация с таким ИНН
        if Organization.objects.filter(inn=registration.inn).exists():
            existing_org = Organization.objects.get(inn=registration.inn)
            messages.info(
                request,
                f'Организация с ИНН {registration.inn} уже существует. Пользователь будет привязан к существующей организации: "{existing_org.short_name}"',
            )

        user, organization = process_approve(registration)

        if Organization.objects.filter(inn=registration.inn).exists():
            messages.success(
                request,
                f'Заявка "{registration.short_name}" одобрена. Пользователь "{user.username}" создан и привязан к существующей организации "{organization.short_name}".',
            )
        else:
            messages.success(
                request,
                f'Заявка "{registration.short_name}" одобрена. Созданы пользователь "{user.username}" и организация "{organization.short_name}".',
            )

    except Exception as e:
        messages.error(request, f"Ошибка: {str(e)}")

    return redirect("admin:accounts_employerregistrationrequest_changelist")


@staff_member_required
def reject_employer_request(request, request_id):
    """Отклонение заявки работодателя"""
    registration = get_object_or_404(
        EmployerRegistrationRequest, id=request_id, status="pending"
    )

    registration.status = "rejected"
    registration.save()

    messages.warning(request, f'Заявка "{registration.short_name}" отклонена.')

    return redirect("admin:accounts_employerregistrationrequest_changelist")


@staff_member_required
def employee_full_profile(request, profile_id):
    """
    Read-only карточка «Полный профиль работника»:
    CustomUser + EmployeeProfile + статусы + опросы + RIASEC + рекомендации + курсы.
    """
    profile = get_object_or_404(
        EmployeeProfile.objects.select_related(
            "user", "user__organization", "desired_organization_type"
        ),
        id=profile_id,
    )
    user = profile.user

    # --- Статусы ---
    profile_complete = profile.is_profile_complete()
    goal_setting_complete = profile.is_goal_setting_complete()

    # --- Каких полей не хватает для is_profile_complete() ---
    missing_fields = []

    if not user.last_name:
        missing_fields.append(("last_name", "Фамилия (пользователь)"))
    if not user.first_name:
        missing_fields.append(("first_name", "Имя (пользователь)"))
    if not user.birthday:
        missing_fields.append(("birthday", "Дата рождения (пользователь)"))

    required_profile = {
        "snils": "СНИЛС",
        "gender": "Пол",
        "citizenship": "Гражданство",
        "education_level": "Уровень образования",
        "graduation_year": "Год окончания",
        "education_institution": "Учебное заведение",
        "specialty": "Специальность",
        "locality": "Населённый пункт",
        "municipality": "Муниципалитет",
    }
    for field, label in required_profile.items():
        if not getattr(profile, field):
            missing_fields.append((field, label))

    if not profile.is_unemployed:
        if not profile.organization_id:
            missing_fields.append(("organization", "Организация"))
        if not profile.position:
            missing_fields.append(("position", "Должность"))
        if not profile.position_level:
            missing_fields.append(("position_level", "Категория должности"))

    # --- Целеполагание ---
    questions = Question.objects.filter(is_active=True)
    total_questions = questions.count()
    answered_responses = GoalSettingResponse.objects.filter(user=user)
    answered_count = answered_responses.count()
    answered_ids = set(answered_responses.values_list("question_id", flat=True))
    unanswered = questions.exclude(id__in=answered_ids)

    # --- Опросы ---
    survey_categories = SurveyCategory.objects.filter(is_active=True)
    surveys_summary = []
    for cat in survey_categories:
        session = (
            SurveySession.objects.filter(user=user, category=cat, status="completed")
            .order_by("-attempt")
            .first()
        )
        surveys_summary.append(
            {
                "category": cat,
                "completed": session is not None,
                "attempt": session.attempt if session else None,
                "completed_at": session.completed_at if session else None,
            }
        )

    # --- RIASEC ---
    riasac = (
        RiasacResult.objects.filter(session__user=user)
        .select_related("session")
        .order_by("-created_at")
        .first()
    )
    riasec_scores = riasac.get_scores_dict() if riasac else {}

    # --- Рекомендации ---
    recommendations = (
        CourseRecommendation.objects.filter(user=user)
        .select_related("course", "course__organization")
        .order_by("order", "-relevance_score")
    )

    # --- Выбранные курсы ---
    selected_courses = (
        SelectedCourse.objects.filter(user=user)
        .select_related("course", "course__organization")
        .prefetch_related("approval")
        .order_by("-created_at")
    )

    context = {
        "profile": profile,
        "u": user,
        "profile_complete": profile_complete,
        "goal_setting_complete": goal_setting_complete,
        "ready_for_recommendations": profile_complete and goal_setting_complete,
        "missing_fields": missing_fields,
        "total_questions": total_questions,
        "answered_count": answered_count,
        "unanswered": unanswered,
        "surveys_summary": surveys_summary,
        "surveys_completed_count": sum(1 for s in surveys_summary if s["completed"]),
        "surveys_total": len(surveys_summary),
        "riasac": riasac,
        "riasec_scores": riasec_scores,
        "recommendations": recommendations,
        "recommendations_count": recommendations.count(),
        "selected_courses": selected_courses,
        "selected_courses_count": selected_courses.count(),
        # --- Для корректной отрисовки админки Jazzmin (сайдбар, шапка) ---
        "available_apps": admin_site.get_app_list(request),
        "app_list": admin_site.get_app_list(request),
        "is_popup": False,
        "is_nav_sidebar_enabled": True,
        "has_permission": True,
        # --- Ссылки ---
        "user_admin_url": reverse("admin:users_customuser_change", args=[user.id]),
        "profile_edit_url": reverse(
            "admin:accounts_employeeprofile_change", args=[profile.id]
        ),
    }
    return render(request, "admin/accounts/employee_full_profile.html", context)
