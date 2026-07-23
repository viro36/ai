import pytest
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.technical_requirements.models import (
    TechnicalRequirement,
    TechnicalRequirementUniversity,
    RequirementStatus,
)
from apps.organizations.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()


pytestmark = pytest.mark.django_db


class TestCreateTechnicalRequirementView:
    """Тесты для создания технического задания"""

    def test_create_view_requires_login(self, client):
        url = reverse("technical_requirements:create")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_create_view_requires_employer(self, client, university_user):
        client.force_login(university_user)
        url = reverse("technical_requirements:create")
        response = client.get(url)
        assert response.status_code == 302
        # Проверяем что редирект на главную
        assert response.url == "/" or "home" in response.url

    def test_create_view_returns_200_for_employer(self, client, employer_user):
        client.force_login(employer_user)
        url = reverse("technical_requirements:create")
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert "questions" in response.context

    def test_create_view_post_valid(
        self,
        client,
        employer_user,
        university_user,
        another_university_user,
        question_text,
        question_textarea,
        question_choice,
        question_multiple_choice,
        question_boolean,
        question_date,
        question_number,
        requirement_status_sent,
    ):
        """Тест успешного создания ТЗ"""
        # Создаем 5 ВУЗов
        universities = [
            university_user.organization,
            another_university_user.organization,
        ]
        for i in range(3, 6):
            org = Organization.objects.create(
                inn=f"{i:012d}",
                short_name=f"Тест ВУЗ {i}",
                full_name=f"Тест ВУЗ полное {i}",
                address_raw="г. Воронеж",
                status="ACTIVE",
            )
            User.objects.create_user(
                username=f"test_univ_{i}",
                email=f"test_univ{i}@test.com",
                password="test123",
                user_type="university",
                organization=org,
            )
            universities.append(org)

        client.force_login(employer_user)
        url = reverse("technical_requirements:create")

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_text.id}": "Тестовый ответ",
            f"q_{question_textarea.id}": "Тестовый ответ textarea",
            f"q_{question_choice.id}": "Автоматизация",
            f"q_{question_multiple_choice.id}": ["Docker"],
            f"q_{question_boolean.id}": True,
            f"q_{question_date.id}": "2024-01-01",
            f"q_{question_number.id}": 10,
        }

        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("technical_requirements:my_requirements")

        # Проверяем, что ТЗ создано
        requirement = TechnicalRequirement.objects.filter(
            employer=employer_user
        ).first()
        assert requirement is not None

        # Проверяем, что созданы связи с ВУЗами
        university_statuses = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=requirement
        )
        assert university_statuses.count() == 5
        # Проверяем, что статус установлен "Отправлено"
        for uni_status in university_statuses:
            assert uni_status.status == requirement_status_sent

    def test_create_view_post_invalid(self, client, employer_user, university_user):
        """Тест отправки невалидной формы"""
        client.force_login(employer_user)
        url = reverse("technical_requirements:create")

        data = {
            "universities": [university_user.organization.id],
        }

        response = client.post(url, data, follow=True)
        assert response.status_code == 200
        # Проверяем, что есть сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        assert any("исправьте ошибки" in str(msg).lower() for msg in messages)


class TestMyRequirementsListView:
    """Тесты для списка ТЗ работодателя"""

    def test_my_requirements_requires_login(self, client):
        url = reverse("technical_requirements:my_requirements")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_my_requirements_returns_200_for_employer(self, client, employer_user):
        client.force_login(employer_user)
        url = reverse("technical_requirements:my_requirements")
        response = client.get(url)
        assert response.status_code == 200
        assert "requirements" in response.context

    def test_my_requirements_shows_only_own_requirements(
        self, client, employer_user, draft_requirement
    ):
        """Показывает только свои ТЗ"""
        # Создаем ТЗ для другого пользователя
        other_user = User.objects.create_user(
            username="other_employer",
            email="other@test.com",
            password="test123",
            user_type="employer",
            last_name="Другой",
            first_name="Пользователь",
        )
        other_org = Organization.objects.create(
            inn="999999999999",
            short_name="Другая ООО",
            full_name="Другая организация",
            address_raw="г. Другой",
            status="ACTIVE",
        )
        other_user.organization = other_org
        other_user.save()

        other_requirement = TechnicalRequirement.objects.create(
            employer=other_user,
            answers={},
        )

        client.force_login(employer_user)
        url = reverse("technical_requirements:my_requirements")
        response = client.get(url)
        assert response.status_code == 200
        requirements = response.context["requirements"]
        assert draft_requirement in requirements
        assert other_requirement not in requirements


class TestReceivedRequirementsListView:
    """Тесты для списка полученных ТЗ для ВУЗа"""

    def test_received_requirements_requires_login(self, client):
        url = reverse("technical_requirements:received_requirements")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_received_requirements_returns_200_for_university(
        self, client, university_user
    ):
        client.force_login(university_user)
        url = reverse("technical_requirements:received_requirements")
        response = client.get(url)
        assert response.status_code == 200
        assert "requirements" in response.context

    def test_received_requirements_shows_only_for_own_university(
        self, client, university_user, another_university_user, technical_requirement
    ):
        """Показывает только ТЗ для своего ВУЗа"""
        # Создаем ТЗ для другого ВУЗа
        other_requirement = TechnicalRequirement.objects.create(
            employer=technical_requirement.employer,
            answers={},
        )
        TechnicalRequirementUniversity.objects.create(
            technical_requirement=other_requirement,
            university=another_university_user.organization,
        )

        client.force_login(university_user)
        url = reverse("technical_requirements:received_requirements")
        response = client.get(url)
        assert response.status_code == 200
        requirements = response.context["requirements"]
        # Теперь requirements содержит TechnicalRequirementUniversity
        assert any(
            req.technical_requirement == technical_requirement for req in requirements
        )
        assert not any(
            req.technical_requirement == other_requirement for req in requirements
        )


class TestRequirementDetailView:
    """Тесты для детального просмотра ТЗ"""

    def test_detail_requires_login(self, client, technical_requirement):
        url = reverse("technical_requirements:detail", args=[technical_requirement.id])
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_detail_returns_200_for_employer(
        self, client, employer_user, technical_requirement
    ):
        client.force_login(employer_user)
        url = reverse("technical_requirements:detail", args=[technical_requirement.id])
        response = client.get(url)
        assert response.status_code == 200
        assert "requirement" in response.context
        assert "questions" in response.context
        assert "university_statuses" in response.context

    def test_detail_returns_200_for_university(
        self, client, university_user, technical_requirement
    ):
        client.force_login(university_user)
        url = reverse("technical_requirements:detail", args=[technical_requirement.id])
        response = client.get(url)
        assert response.status_code == 200

    def test_detail_returns_404_for_wrong_user(
        self, client, another_university_user, technical_requirement
    ):
        """Пользователь не видит чужое ТЗ"""
        client.force_login(another_university_user)
        url = reverse("technical_requirements:detail", args=[technical_requirement.id])
        response = client.get(url)
        assert response.status_code == 404


class TestDeleteTechnicalRequirementView:
    """Тесты для удаления ТЗ"""

    def test_delete_requires_login(self, client, draft_requirement):
        url = reverse("technical_requirements:delete", args=[draft_requirement.id])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_delete_success(self, client, employer_user, draft_requirement):
        client.force_login(employer_user)
        url = reverse("technical_requirements:delete", args=[draft_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert not TechnicalRequirement.objects.filter(id=draft_requirement.id).exists()


class TestUpdateRequirementStatusView:
    """Тесты для обновления статуса ТЗ для ВУЗа"""

    def test_update_status_requires_login(
        self, client, technical_requirement, university_user
    ):
        uni_status = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=technical_requirement,
            university=university_user.organization,
        ).first()
        url = reverse("technical_requirements:update_status", args=[uni_status.id])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_update_status_requires_university(
        self, client, employer_user, technical_requirement, university_user
    ):
        """Только ВУЗ может изменять статус"""
        uni_status = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=technical_requirement,
            university=university_user.organization,
        ).first()
        client.force_login(employer_user)
        url = reverse("technical_requirements:update_status", args=[uni_status.id])
        response = client.post(url, follow=True)
        # Проверяем что доступ запрещен (403) или редирект
        assert response.status_code in [403, 302]

    def test_update_status_success(
        self, client, university_user, technical_requirement, requirement_status_sent
    ):
        """Тест успешного обновления статуса"""
        # Создаем еще один статус
        status_in_development = RequirementStatus.objects.create(
            code=2,
            name="В разработке",
            color="#ffc107",
            order=2,
        )

        uni_status = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=technical_requirement,
            university=university_user.organization,
        ).first()

        # Проверяем, что статус сейчас "Отправлено"
        assert uni_status.status == requirement_status_sent

        client.force_login(university_user)
        url = reverse("technical_requirements:update_status", args=[uni_status.id])

        # Отправляем POST запрос
        data = {"status_id": status_in_development.id}
        response = client.post(url, data, follow=True)
        assert response.status_code == 200

        # Проверяем сообщение об успехе
        messages = list(get_messages(response.wsgi_request))
        assert any("изменён" in str(msg) for msg in messages)

        # Получаем объект заново из БД
        updated_status = TechnicalRequirementUniversity.objects.get(pk=uni_status.pk)
        assert updated_status.status == status_in_development

    def test_update_status_wrong_university(
        self, client, another_university_user, technical_requirement, university_user
    ):
        """ВУЗ не может изменить статус чужого ТЗ"""
        uni_status = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=technical_requirement,
            university=university_user.organization,
        ).first()

        client.force_login(another_university_user)
        url = reverse("technical_requirements:update_status", args=[uni_status.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("нет доступа" in str(msg).lower() for msg in messages)


class TestRequirementStatusesView:
    """Тесты для просмотра статусов ТЗ по ВУЗам"""

    def test_statuses_requires_login(self, client, technical_requirement):
        url = reverse(
            "technical_requirements:requirement_statuses",
            args=[technical_requirement.id],
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_statuses_requires_employer(
        self, client, university_user, technical_requirement
    ):
        """Только работодатель может видеть статусы всех ВУЗов"""
        client.force_login(university_user)
        url = reverse(
            "technical_requirements:requirement_statuses",
            args=[technical_requirement.id],
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_statuses_returns_200_for_employer(
        self, client, employer_user, technical_requirement
    ):
        client.force_login(employer_user)
        url = reverse(
            "technical_requirements:requirement_statuses",
            args=[technical_requirement.id],
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "requirement" in response.context
        assert "university_statuses" in response.context
