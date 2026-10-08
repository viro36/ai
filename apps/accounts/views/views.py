from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.views.decorators.http import require_POST
from apps.organizations.models import District, Organization, OrganizationType
from ..forms import (
    EmployeeProfileForm,
    EmployeeRegistrationForm,
    EmployerProfileForm,
    EmployerRegistrationForm,
)
from ..models import (
    EmployeeProfile,
    EmployerProfile,
    EmployerRegistrationRequest,
    Position,
)

User = get_user_model()


def employer_register(request):
    """Регистрация работодателя"""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = EmployerRegistrationForm(request.POST)
        if form.is_valid():
            registration = EmployerRegistrationRequest.objects.create(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=make_password(form.cleaned_data["password"]),
                short_name=form.cleaned_data["short_name"],
                full_name=form.cleaned_data["full_name"],
                inn=form.cleaned_data["inn"],
                status="pending",
            )
            messages.success(
                request,
                "Ваша заявка отправлена на рассмотрение администратору. "
                "Вы получите уведомление на email после принятия решения.",
            )
            return redirect("login")
    else:
        form = EmployerRegistrationForm()

    return render(request, "accounts/employer/employer_register.html", {"form": form})


@staff_member_required
def employer_requests_list(request):
    """Список заявок на регистрацию (для админа)"""
    pending_requests = EmployerRegistrationRequest.objects.filter(status="pending")
    approved_requests = EmployerRegistrationRequest.objects.filter(status="approved")[
        :20
    ]
    rejected_requests = EmployerRegistrationRequest.objects.filter(status="rejected")[
        :20
    ]

    context = {
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
    }
    return render(request, "accounts/employer/employer_requests_list.html", context)


@staff_member_required
@require_POST
def approve_employer_request(request, request_id):
    """Одобрение заявки работодателя"""
    registration = get_object_or_404(
        EmployerRegistrationRequest, id=request_id, status="pending"
    )

    try:
        # Проверяем, не существует ли уже организация с таким ИНН
        if Organization.objects.filter(inn=registration.inn).exists():
            messages.error(
                request,
                f"Организация с ИНН {registration.inn} уже существует в системе.",
            )
            registration.status = "rejected"
            registration.save()
            return redirect("employer_requests_list")

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

        # Устанавливаем тип пользователя
        if hasattr(user, "user_type"):
            user.user_type = "employer"
            user.save()

        registration.status = "approved"
        registration.created_user = user
        registration.created_organization = organization
        registration.save()

        messages.success(request, f'Заявка "{registration.short_name}" одобрена.')

    except Exception as e:
        messages.error(request, f"Ошибка при одобрении заявки: {str(e)}")

    return redirect("accounts:employer_requests_list")


@staff_member_required
@require_POST
def reject_employer_request(request, request_id):
    """Отклонение заявки работодателя"""
    registration = get_object_or_404(
        EmployerRegistrationRequest, id=request_id, status="pending"
    )

    registration.status = "rejected"
    registration.save()

    messages.warning(request, f'Заявка "{registration.short_name}" отклонена.')

    return redirect("accounts:employer_requests_list")


# -------------------------------------------------------------------------------------------


@login_required
def employer_profile(request):
    """Редактирование профиля организации (работодатель / ВУЗ)"""
    if request.user.user_type not in ["employer", "university"]:
        messages.error(request, "Доступ запрещён. Только для работодателей или ВУЗов.")
        return redirect("home")

    # Получаем или создаём профиль
    profile, created = EmployerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = EmployerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # Обновляем email пользователя (регистрационный)
            request.user.email = form.cleaned_data["registration_email"]
            request.user.save()

            # Сохраняем профиль
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            messages.success(request, "Профиль успешно обновлён!")
            return redirect("accounts:employer_profile")
    else:
        initial_data = {
            "registration_email": request.user.email,
        }
        form = EmployerProfileForm(instance=profile, initial=initial_data)

    # Получаем данные организации из DaData
    organization = request.user.organization

    context = {
        "form": form,
        "profile": profile,
        "organization": organization,
        "is_university": request.user.user_type == "university",
    }
    return render(request, "accounts/employer/employer_profile.html", context)


# -------------------------------------------------------------------------------------------


def employee_register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                patronymic=form.cleaned_data["patronymic"],
                snils=form.cleaned_data["snils"],
                organization=profile.organization,  # может быть None
                user_type="employee",
            )

            profile.user = user
            profile.snils = form.cleaned_data["snils"]
            profile.save()

            login(request, user)

            if form.cleaned_data.get("is_unemployed"):
                messages.success(
                    request,
                    f"Добро пожаловать, {user.get_full_name()}! "
                    f"Вы зарегистрированы как безработный.",
                )
            else:
                position_display = dict(EmployeeProfile.POSITION_LEVEL_CHOICES).get(
                    form.cleaned_data["position_level"], form.cleaned_data["position"]
                )
                messages.success(
                    request,
                    f"Добро пожаловать, {user.get_full_name()}! "
                    f"Вы зарегистрированы как {position_display} "
                    f'в организации "{profile.organization.short_name}".',
                )
            return redirect("home")
    else:
        form = EmployeeRegistrationForm()

    context = {
        "form": form,
        "districts": District.objects.all(),
        "organization_types": OrganizationType.objects.all(),
    }
    return render(request, "accounts/employee/employee_register.html", context)


def get_organizations_ajax(request):
    """AJAX для получения отфильтрованного списка организаций"""
    district_id = request.GET.get("district_id")
    org_type_id = request.GET.get("org_type_id")

    organizations = Organization.objects.select_related(
        "district", "organization_type"
    ).all()

    if district_id:
        organizations = organizations.filter(district_id=district_id)
    if org_type_id:
        organizations = organizations.filter(organization_type_id=org_type_id)

    organizations = organizations.order_by("short_name")

    data = {
        "organizations": [
            {
                "id": org.id,
                "text": (
                    f"{org.short_name} "
                    f"({org.district.short_name if org.district else 'без района'})"
                ),
                "inn": org.inn,
                "organization_type_id": org.organization_type_id or "",
                "organization_type_name": (
                    org.organization_type.name if org.organization_type else ""
                ),
            }
            for org in organizations
        ]
    }
    return JsonResponse(data)


# -------------------------------------------------------------------------------------------


@login_required
def employee_profile(request):
    if request.user.user_type != "employee":
        messages.error(request, "Доступ запрещён. Только для работников.")
        return redirect("home")

    profile = request.user.employee_profile
    user = request.user

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST, instance=profile)
        if form.is_valid():
            # Обновляем user
            user.last_name = form.cleaned_data["last_name"]
            user.first_name = form.cleaned_data["first_name"]
            user.patronymic = form.cleaned_data["patronymic"]
            user.birthday = form.cleaned_data["birthday"]
            user.snils = form.cleaned_data["snils"]
            user.email = form.cleaned_data["email"]
            user.save()

            profile = form.save(commit=False)

            # Организация — из organization_id
            if profile.is_unemployed:
                profile.organization = None
            else:
                organization_id = request.POST.get("organization_id")
                if organization_id:
                    try:
                        profile.organization = Organization.objects.get(
                            id=organization_id
                        )
                    except Organization.DoesNotExist:
                        pass

            profile.save()

            messages.success(request, "Профиль успешно обновлён!")
            return redirect("accounts:employee_profile")
    else:
        initial_data = {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "patronymic": user.patronymic,
            "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else None,
            "snils": user.snils,
            "email": user.email,
            "position": profile.position,
            "position_level": profile.position_level,
            "gender": profile.gender,
            "citizenship": profile.citizenship,
            "phone": profile.phone,
            "municipality": profile.municipality,
            "locality": profile.locality,
            "employment_status": profile.employment_status,
            "work_experience_years": profile.work_experience_years,
            "education_level": profile.education_level,
            "education_institution": profile.education_institution,
            "graduation_year": profile.graduation_year,
            "specialty": profile.specialty,
            "organization": profile.organization_id if profile.organization else None,
            "is_unemployed": profile.is_unemployed,
            "is_svo_participant": profile.is_svo_participant,
            "desired_organization_type": profile.desired_organization_type_id,
            "desired_organization": profile.desired_organization,
            "desired_position": profile.desired_position,
        }
        form = EmployeeProfileForm(initial=initial_data, instance=profile)

    context = {
        "form": form,
        "profile": profile,
        "districts": District.objects.all(),
        "organization_types": OrganizationType.objects.all(),
    }
    return render(request, "accounts/employee/employee_profile.html", context)


def get_positions_ajax(request):
    """
    AJAX: возвращает должности по категории и (опционально) типу организации.

    Логика:
    - Если тип организации передан и у него есть свой справочник — вернуть его + универсальные.
    - Если тип не передан или у него нет своего справочника — вернуть только универсальные.
    """
    position_level = request.GET.get("position_level")
    org_type_id = request.GET.get("organization_type_id")

    positions = Position.objects.filter(is_active=True)

    if position_level:
        positions = positions.filter(position_level=position_level)

    if org_type_id:
        positions = positions.filter(
            Q(organization_type_id=org_type_id) | Q(organization_type__isnull=True)
        )
    else:
        positions = positions.filter(organization_type__isnull=True)

    positions = positions.order_by("sort_order", "name")

    return JsonResponse(
        {"positions": [{"id": p.id, "text": p.name} for p in positions]}
    )
