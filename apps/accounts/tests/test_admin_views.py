import pytest
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.messages import get_messages
from apps.organizations.models import Organization
from apps.accounts.models import EmployerRegistrationRequest
from apps.users.models import CustomUser


@pytest.mark.django_db
class TestProcessApprove:
    """Тесты для функции process_approve"""

    def test_process_approve_new_organization(self, test_organization):
        """Тест одобрения заявки с новой организацией"""
        registration = EmployerRegistrationRequest.objects.create(
            username="new_employer",
            email="new@test.com",
            password=make_password("testpass"),
            short_name="ООО Новая",
            full_name="Общество с ограниченной ответственностью Новая",
            inn="999999999999",
            status="pending",
        )

        from apps.accounts.admin_views import process_approve

        user, organization = process_approve(registration)

        # Проверяем, что организация создалась
        assert Organization.objects.filter(inn="999999999999").exists()
        assert organization.inn == "999999999999"

        # Проверяем, что пользователь создался
        assert CustomUser.objects.filter(username="new_employer").exists()
        assert user.username == "new_employer"
        assert user.user_type == "employer"
        assert user.organization == organization

        # Проверяем, что заявка обновлена
        registration.refresh_from_db()
        assert registration.status == "approved"
        assert registration.created_user == user
        assert registration.created_organization == organization

    def test_process_approve_existing_organization(self, test_organization):
        """Тест одобрения заявки с уже существующей организацией"""
        registration = EmployerRegistrationRequest.objects.create(
            username="existing_org_employer",
            email="existing@test.com",
            password=make_password("testpass"),
            short_name="ООО Существующая",
            full_name="Общество с ограниченной ответственностью Существующая",
            inn=test_organization.inn,
            status="pending",
        )

        from apps.accounts.admin_views import process_approve

        user, organization = process_approve(registration)

        # Проверяем, что новая организация НЕ создалась
        assert Organization.objects.filter(inn=test_organization.inn).count() == 1

        # Проверяем, что пользователь привязан к существующей организации
        assert user.organization == test_organization
        assert user.organization.inn == test_organization.inn

        # Проверяем, что заявка обновлена
        registration.refresh_from_db()
        assert registration.status == "approved"
        assert registration.created_user == user
        assert registration.created_organization == test_organization


@pytest.mark.django_db
class TestApproveEmployerRequestAdminView:
    """Тесты для approve_employer_request в admin_views"""

    def test_approve_employer_request_success(self, admin_client):
        """Успешное одобрение заявки"""
        registration = EmployerRegistrationRequest.objects.create(
            username="approve_test",
            email="approve@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789099",
            status="pending",
        )

        url = reverse("admin:approve_employer_request", args=[registration.id])
        response = admin_client.post(url)

        # Проверяем редирект
        assert response.status_code == 302
        assert response.url == reverse(
            "admin:accounts_employerregistrationrequest_changelist"
        )

        # Проверяем, что заявка одобрена
        registration.refresh_from_db()
        assert registration.status == "approved"

        # Проверяем, что пользователь и организация созданы
        assert CustomUser.objects.filter(username="approve_test").exists()
        assert Organization.objects.filter(inn="123456789099").exists()

        # Проверяем сообщение об успехе
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert "одобрена" in messages[0].message

    def test_approve_employer_request_already_exists(
        self, admin_client, test_organization
    ):
        """Одобрение заявки с уже существующей организацией"""
        registration = EmployerRegistrationRequest.objects.create(
            username="approve_existing",
            email="approve_existing@test.com",
            password=make_password("testpass"),
            short_name="ООО Существующее",
            full_name="Общество с ограниченной ответственностью Существующее",
            inn=test_organization.inn,
            status="pending",
        )

        url = reverse("admin:approve_employer_request", args=[registration.id])
        response = admin_client.post(url)

        assert response.status_code == 302

        registration.refresh_from_db()
        assert registration.status == "approved"

        # Проверяем, что новая организация не создалась
        assert Organization.objects.filter(inn=test_organization.inn).count() == 1

        # Проверяем, что пользователь привязан к существующей организации
        user = CustomUser.objects.get(username="approve_existing")
        assert user.organization == test_organization

    def test_approve_employer_request_not_found(self, admin_client):
        """Одобрение несуществующей заявки"""
        url = reverse("admin:approve_employer_request", args=[99999])
        response = admin_client.post(url)

        # Должен быть 404
        assert response.status_code == 404

    def test_approve_employer_request_already_processed(self, admin_client):
        """Одобрение уже обработанной заявки"""
        registration = EmployerRegistrationRequest.objects.create(
            username="already_processed",
            email="processed@test.com",
            password=make_password("testpass"),
            short_name="ООО Обработанное",
            full_name="Общество с ограниченной ответственностью Обработанное",
            inn="123456789088",
            status="approved",  # Уже одобрена
        )

        url = reverse("admin:approve_employer_request", args=[registration.id])
        response = admin_client.post(url)

        # Должен быть 404, так как статус не pending
        assert response.status_code == 404


@pytest.mark.django_db
class TestRejectEmployerRequestAdminView:
    """Тесты для reject_employer_request в admin_views"""

    def test_reject_employer_request_success(self, admin_client):
        """Успешное отклонение заявки"""
        registration = EmployerRegistrationRequest.objects.create(
            username="reject_test",
            email="reject@test.com",
            password=make_password("testpass"),
            short_name="ООО Отклоняемое",
            full_name="Общество с ограниченной ответственностью Отклоняемое",
            inn="123456789077",
            status="pending",
        )

        url = reverse("admin:reject_employer_request", args=[registration.id])
        response = admin_client.post(url)

        assert response.status_code == 302
        assert response.url == reverse(
            "admin:accounts_employerregistrationrequest_changelist"
        )

        registration.refresh_from_db()
        assert registration.status == "rejected"

        # Проверяем сообщение
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert "отклонена" in messages[0].message

    def test_reject_employer_request_not_found(self, admin_client):
        """Отклонение несуществующей заявки"""
        url = reverse("admin:reject_employer_request", args=[99999])
        response = admin_client.post(url)

        assert response.status_code == 404

    def test_reject_employer_request_already_processed(self, admin_client):
        """Отклонение уже обработанной заявки"""
        registration = EmployerRegistrationRequest.objects.create(
            username="already_rejected",
            email="rejected@test.com",
            password=make_password("testpass"),
            short_name="ООО Отклонённое",
            full_name="Общество с ограниченной ответственностью Отклонённое",
            inn="123456789066",
            status="rejected",  # Уже отклонена
        )

        url = reverse("admin:reject_employer_request", args=[registration.id])
        response = admin_client.post(url)

        assert response.status_code == 404
