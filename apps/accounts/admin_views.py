from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from apps.organizations.models import Organization
from .models import EmployerRegistrationRequest

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
