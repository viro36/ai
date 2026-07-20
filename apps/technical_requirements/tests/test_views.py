import pytest
import json
from django.urls import reverse
from django.contrib.messages import get_messages

from apps.technical_requirements.models import TechnicalRequirement
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
        assert TechnicalRequirement.objects.filter(employer=employer_user).exists()

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


class TestEditTechnicalRequirementView:
    """Тесты для редактирования технического задания"""

    def test_edit_view_requires_login(self, client, draft_requirement):
        url = reverse("technical_requirements:edit", args=[draft_requirement.id])
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_edit_view_requires_employer(
        self, client, university_user, draft_requirement
    ):
        client.force_login(university_user)
        url = reverse("technical_requirements:edit", args=[draft_requirement.id])
        response = client.get(url)
        assert response.status_code == 404

    def test_edit_view_returns_200_for_employer(
        self, client, employer_user, draft_requirement
    ):
        client.force_login(employer_user)
        url = reverse("technical_requirements:edit", args=[draft_requirement.id])
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert "requirement" in response.context

    def test_edit_view_cannot_edit_sent_requirement(
        self, client, employer_user, technical_requirement
    ):
        """Нельзя редактировать отправленное ТЗ"""
        client.force_login(employer_user)
        url = reverse("technical_requirements:edit", args=[technical_requirement.id])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("technical_requirements:my_requirements")

    def test_edit_view_post_valid(
        self,
        client,
        employer_user,
        draft_requirement,
        question_text,
        question_textarea,
        question_choice,
        question_multiple_choice,
        question_boolean,
        question_date,
        question_number,
        question_depends_on,
    ):
        """Тест успешного редактирования ТЗ"""
        # Добавляем 5 ВУЗов
        from django.contrib.auth import get_user_model

        User = get_user_model()

        universities = list(draft_requirement.universities.all())
        for i in range(5 - len(universities)):
            org = Organization.objects.create(
                inn=f"{i+1:012d}",
                short_name=f"Тест ВУЗ {i+1}",
                full_name=f"Тест ВУЗ полное {i+1}",
                address_raw="г. Воронеж",
                status="ACTIVE",
            )
            User.objects.create_user(
                username=f"test_univ_{i+1}",
                email=f"test_univ{i+1}@test.com",
                password="test123",
                user_type="university",
                organization=org,
            )
            draft_requirement.universities.add(org)
            universities.append(org)

        client.force_login(employer_user)
        url = reverse("technical_requirements:edit", args=[draft_requirement.id])

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_text.id}": "Обновленный ответ",
            f"q_{question_textarea.id}": "Обновленный ответ textarea",
            f"q_{question_choice.id}": "Внедрение ИИ",
            f"q_{question_multiple_choice.id}": ["Docker"],
            f"q_{question_boolean.id}": True,
            f"q_{question_date.id}": "2024-01-01",
            f"q_{question_number.id}": 10,
            f"q_{question_depends_on.id}": "Тестовая площадка",
        }

        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("technical_requirements:my_requirements")

        draft_requirement.refresh_from_db()
        answers = json.loads(draft_requirement.answers)
        assert answers[str(question_text.id)] == "Обновленный ответ"


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
            status="draft",
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
            status="sent",
        )
        other_requirement.universities.add(another_university_user.organization)

        client.force_login(university_user)
        url = reverse("technical_requirements:received_requirements")
        response = client.get(url)
        assert response.status_code == 200
        requirements = response.context["requirements"]
        assert technical_requirement in requirements
        assert other_requirement not in requirements


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

    def test_delete_only_draft(self, client, employer_user, technical_requirement):
        """Нельзя удалить отправленное ТЗ"""
        client.force_login(employer_user)
        url = reverse("technical_requirements:delete", args=[technical_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("Нельзя удалить" in str(msg) for msg in messages)
        assert TechnicalRequirement.objects.filter(id=technical_requirement.id).exists()

    def test_delete_success(self, client, employer_user, draft_requirement):
        client.force_login(employer_user)
        url = reverse("technical_requirements:delete", args=[draft_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert not TechnicalRequirement.objects.filter(id=draft_requirement.id).exists()


class TestSendTechnicalRequirementView:
    """Тесты для отправки ТЗ"""

    def test_send_requires_login(self, client, draft_requirement):
        url = reverse("technical_requirements:send", args=[draft_requirement.id])
        response = client.post(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_send_only_draft(self, client, employer_user, technical_requirement):
        """Нельзя отправить уже отправленное ТЗ"""
        client.force_login(employer_user)
        url = reverse("technical_requirements:send", args=[technical_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        assert any("уже отправлено" in str(msg).lower() for msg in messages)

    def test_send_requires_5_universities(
        self, client, employer_user, draft_requirement
    ):
        """Нельзя отправить если менее 5 ВУЗов"""
        client.force_login(employer_user)
        url = reverse("technical_requirements:send", args=[draft_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200
        messages = list(get_messages(response.wsgi_request))
        # Проверяем что есть сообщение о необходимости 5 ВУЗов
        assert any("5 ВУЗов" in str(msg) for msg in messages)

    def test_send_success(
        self,
        client,
        employer_user,
        draft_requirement,
        university_user,
        another_university_user,
    ):
        """Тест успешной отправки ТЗ"""
        # Добавляем 5 ВУЗов
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

        for u in universities:
            draft_requirement.universities.add(u)

        client.force_login(employer_user)
        url = reverse("technical_requirements:send", args=[draft_requirement.id])
        response = client.post(url, follow=True)
        assert response.status_code == 200

        draft_requirement.refresh_from_db()
        assert draft_requirement.status == "sent"
