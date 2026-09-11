from django.utils import timezone
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from apps.courses.models import Course
from apps.organizations.models import Organization
from apps.accounts.models import (
    EmployerRegistrationRequest,
    EmployerProfile,
    EmployeeProfile,
)
from apps.recommendations.models import CourseRecommendation, SelectedCourse

User = get_user_model()


@pytest.mark.django_db
class TestEmployerRegisterView:
    """Тесты для регистрации работодателя"""

    def test_employer_register_get(self, client):
        url = reverse("accounts:employer_register")
        response = client.get(url)
        assert response.status_code == 200
        assert "accounts/employer/employer_register.html" in [
            t.name for t in response.templates
        ]

    def test_employer_register_post_valid(self, client):
        url = reverse("accounts:employer_register")
        data = {
            "username": "test_employer",
            "email": "employer@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "short_name": "ООО Тест",
            "full_name": "Общество с ограниченной ответственностью Тест",
            "inn": "123456789012",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("login")
        assert EmployerRegistrationRequest.objects.filter(
            username="test_employer"
        ).exists()


@pytest.mark.django_db
class TestEmployeeRegisterView:
    """Тесты для регистрации работника"""

    def test_employee_register_get(self, client, test_organization):
        url = reverse("accounts:employee_register")
        response = client.get(url)
        assert response.status_code == 200

    def test_employee_register_post_valid(self, client, test_organization):
        url = reverse("accounts:employee_register")
        data = {
            "username": "test_employee",
            "email": "employee@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "snils": "123-456-789 01",
            "phone": "+7 999 123-45-67",
            "organization": test_organization.id,
            "position": "Инженер",
            "position_level": "specialist",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("home")
        assert User.objects.filter(username="test_employee").exists()


@pytest.mark.django_db
class TestEmployerRequestsListView:
    """Тесты для списка заявок (админ)"""

    def test_employer_requests_list_requires_staff(self, client, regular_user):
        """Доступ только для staff"""
        client.login(username=regular_user.username, password="regular123")
        url = reverse("accounts:employer_requests_list")
        response = client.get(url)
        assert response.status_code == 302  # Редирект на login

    def test_employer_requests_list_staff_access(self, admin_client):
        """Staff имеет доступ"""
        url = reverse("accounts:employer_requests_list")
        response = admin_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestApproveEmployerRequest:
    """Тесты для одобрения заявки"""

    def test_approve_employer_request(self, admin_client):
        """Одобрение заявки"""
        request_obj = EmployerRegistrationRequest.objects.create(
            username="pending_employer",
            email="pending@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест",
            full_name="Общество с ограниченной ответственностью Тест",
            inn="123456789012",
            status="pending",
        )

        url = reverse("accounts:approve_employer_request", args=[request_obj.id])
        response = admin_client.post(url)

        # Перенаправление на список заявок
        assert response.status_code == 302
        assert response.url == reverse("accounts:employer_requests_list")

        request_obj.refresh_from_db()
        assert request_obj.status == "approved"
        assert User.objects.filter(username="pending_employer").exists()
        assert Organization.objects.filter(inn="123456789012").exists()

    def test_approve_employer_request_already_exists(
        self, admin_client, test_organization
    ):
        """Одобрение заявки с уже существующей организацией"""
        request_obj = EmployerRegistrationRequest.objects.create(
            username="pending_employer2",
            email="pending2@test.com",
            password=make_password("testpass"),
            short_name="ООО Тест2",
            full_name="Общество с ограниченной ответственностью Тест2",
            inn=test_organization.inn,
            status="pending",
        )

        url = reverse("accounts:approve_employer_request", args=[request_obj.id])
        response = admin_client.post(url)
        assert response.status_code == 302

        request_obj.refresh_from_db()
        assert request_obj.status == "rejected"


@pytest.mark.django_db
class TestEmployerProfileView:
    """Тесты для профиля работодателя/ВУЗа"""

    def test_employer_profile_requires_login(self, client):
        url = reverse("accounts:employer_profile")
        response = client.get(url)
        assert response.status_code == 302

    def test_employer_profile_requires_correct_user_type(
        self, client, test_employee_user
    ):
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employer_profile")
        response = client.get(url)
        assert response.status_code == 302

    def test_employer_profile_get(self, client, test_employer_user):
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employer_profile")
        response = client.get(url)
        assert response.status_code == 200

    def test_employer_profile_post(self, client, test_employer_user):
        client.login(username=test_employer_user.username, password="testpass123")
        EmployerProfile.objects.create(user=test_employer_user)

        url = reverse("accounts:employer_profile")
        data = {
            "registration_email": "newemail@test.com",
            "phone": "+7 999 888-77-66",
            "website": "https://new-site.com",
            "employee_count": 150,
        }
        response = client.post(url, data)
        assert response.status_code == 302


@pytest.mark.django_db
class TestEmployeeProfileView:
    """Тесты для профиля работника"""

    def test_employee_profile_requires_login(self, client):
        url = reverse("accounts:employee_profile")
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_profile_requires_employee_type(self, client, test_employer_user):
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        response = client.get(url)
        assert response.status_code == 302

    def test_employee_profile_get(self, client, test_employee_user, test_organization):
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        response = client.get(url)
        assert response.status_code == 200

    def test_employee_profile_post(
        self, client, test_employee_user, test_organization, test_organization_type
    ):
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        data = {
            "last_name": "Петров",
            "first_name": "Петр",
            "patronymic": "Петрович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "newemail@test.com",
            "position": "Старший инженер",
            "position_level": "specialist",
            "phone": "+7 999 888-77-66",
            "organization_id": test_organization.id,
            # Новые поля
            "desired_organization_type": test_organization_type.id,
            "desired_organization": "ООО ТехноИнновации",
            "desired_position": "Руководитель IT-отдела",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        # Проверяем, что новые поля сохранились
        profile = EmployeeProfile.objects.get(user=test_employee_user)
        assert profile.desired_organization_type == test_organization_type
        assert profile.desired_organization == "ООО ТехноИнновации"
        assert profile.desired_position == "Руководитель IT-отдела"

    def test_employee_profile_post_empty_desired_fields(
        self, client, test_employee_user, test_organization
    ):
        """Тест сохранения с пустыми желаемыми полями"""
        EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        data = {
            "last_name": "Петров",
            "first_name": "Петр",
            "patronymic": "Петрович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "newemail@test.com",
            "position": "Старший инженер",
            "position_level": "specialist",
            "phone": "+7 999 888-77-66",
            "organization_id": test_organization.id,
            "desired_organization_type": "",
            "desired_organization": "",
            "desired_position": "",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        # Проверяем, что новые поля остались пустыми
        profile = EmployeeProfile.objects.get(user=test_employee_user)
        assert profile.desired_organization_type is None
        assert profile.desired_organization is None
        assert profile.desired_position is None


@pytest.mark.django_db
class TestGetOrganizationsAjax:
    """Тесты для AJAX получения организаций"""

    def test_get_organizations_ajax_no_filters(self, client, test_organization):
        url = reverse("accounts:get_organizations_ajax")
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data

    def test_get_organizations_ajax_with_district_filter(
        self, client, test_organization, test_district
    ):
        url = reverse("accounts:get_organizations_ajax")
        response = client.get(url, {"district_id": test_district.id})
        assert response.status_code == 200

    def test_get_organizations_ajax_with_type_filter(
        self, client, test_organization, test_organization_type
    ):
        url = reverse("accounts:get_organizations_ajax")
        response = client.get(url, {"org_type_id": test_organization_type.id})
        assert response.status_code == 200


@pytest.mark.django_db
class TestEmployeeListView:
    """Тесты для списка работников организации"""

    def test_employee_list_requires_login(self, client):
        """Тест требования авторизации"""
        url = reverse("accounts:employee_list")
        response = client.get(url)
        assert response.status_code in [302, 403]
        if response.status_code == 302:
            assert "/login/" in response.url
        elif response.status_code == 403:
            assert "Доступ запрещён" in response.content.decode()

    def test_employee_list_requires_employer_type(self, client, test_employee_user):
        """Тест - только работодатель имеет доступ"""
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_employee_list_returns_200_for_employer(self, client, test_employer_user):
        """Тест успешного доступа для работодателя"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_employee_list_displays_employees(
        self, client, test_employer_user, test_organization
    ):
        """Тест отображения сотрудников организации"""
        # Создаём сотрудников
        employee1 = User.objects.create_user(
            username="employee1",
            email="emp1@test.com",
            password="pass123",
            first_name="Иван",
            last_name="Петров",
            patronymic="Иванович",
            user_type="employee",
            organization=test_organization,
        )
        EmployeeProfile.objects.create(
            user=employee1,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )

        employee2 = User.objects.create_user(
            username="employee2",
            email="emp2@test.com",
            password="pass123",
            first_name="Мария",
            last_name="Сидорова",
            patronymic="Петровна",
            user_type="employee",
            organization=test_organization,
        )
        EmployeeProfile.objects.create(
            user=employee2,
            snils="987-654-321 01",
            organization=test_organization,
            position="Бухгалтер",
            position_level="specialist",
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Петров" in content
        assert "Сидорова" in content

    def test_employee_list_search(self, client, test_employer_user, test_organization):
        """Тест поиска сотрудников"""
        employee = User.objects.create_user(
            username="search_employee",
            email="search@test.com",
            password="pass123",
            first_name="Поисковый",
            last_name="Тестов",
            user_type="employee",
            organization=test_organization,
        )
        EmployeeProfile.objects.create(
            user=employee,
            snils="111-222-333 01",
            organization=test_organization,
            position="Тестировщик",
            position_level="specialist",
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url, {"search": "Тестов"})

        assert response.status_code == 200
        assert "Тестов" in response.content.decode()

    def test_employee_list_pagination(
        self, client, test_employer_user, test_organization
    ):
        """Тест пагинации списка сотрудников"""
        # Создаём 25 сотрудников
        for i in range(25):
            emp = User.objects.create_user(
                username=f"employee_{i}",
                email=f"emp{i}@test.com",
                password="pass123",
                last_name=f"Фамилия{i}",
                first_name=f"Имя{i}",
                user_type="employee",
                organization=test_organization,
            )
            EmployeeProfile.objects.create(
                user=emp,
                snils=f"{i:03d}-456-789 01",
                organization=test_organization,
                position=f"Должность{i}",
                position_level="specialist",
            )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url, {"page": 2})

        assert response.status_code == 200
        assert "page_obj" in response.context

    def test_employee_list_empty(self, client, test_employer_user):
        """Тест когда нет сотрудников"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Нет сотрудников" in content or "0" in content

    def test_employee_list_recommendations_count(
        self, client, test_employer_user, test_employee_user, test_course
    ):
        """Тест подсчёта количества рекомендаций у сотрудника"""
        # Создаём рекомендации для сотрудника
        for i in range(5):
            CourseRecommendation.objects.create(
                user=test_employee_user,
                course=test_course,
                reason=f"Тестовая причина {i}",
                relevance_score=0.8,
                order=i,
            )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        # Проверяем, что в контексте есть аннотация с количеством
        employees = response.context["employees"]
        for emp in employees:
            if emp.id == test_employee_user.id:
                assert emp.recommendations_count == 5

    def test_employee_list_selected_courses_count(
        self, client, test_employer_user, test_employee_user, test_course
    ):
        """Тест подсчёта количества выбранных курсов у сотрудника"""
        # Создаём выбранные курсы для сотрудника
        for i in range(3):
            course = Course.objects.create(
                title=f"Выбранный курс {i}",
                organization=test_employee_user.organization,
                url=f"https://test.com/course{i}",
                is_deleted=False,
            )
            SelectedCourse.objects.create(
                user=test_employee_user,
                course=course,
            )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        employees = response.context["employees"]
        for emp in employees:
            if emp.id == test_employee_user.id:
                assert emp.selected_courses_count == 3
                assert emp.has_selected_courses is True

    def test_employee_list_no_recommendations(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест когда у сотрудника нет рекомендаций"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        employees = response.context["employees"]
        for emp in employees:
            if emp.id == test_employee_user.id:
                assert emp.recommendations_count == 0

    def test_employee_list_no_selected_courses(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест когда у сотрудника нет выбранных курсов"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        employees = response.context["employees"]
        for emp in employees:
            if emp.id == test_employee_user.id:
                assert emp.selected_courses_count == 0
                assert emp.has_selected_courses is False


@pytest.mark.django_db
class TestEmployeeSelectedCoursesView:
    """Тесты для просмотра выбранных курсов сотрудника работодателем"""

    def test_employee_selected_courses_requires_login(self, client, test_employee_user):
        """Тест требования авторизации"""
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)
        assert response.status_code in [302, 403]

    def test_employee_selected_courses_requires_employer_type(
        self, client, test_employee_user
    ):
        """Тест - только работодатель имеет доступ"""
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_employee_selected_courses_returns_200_for_employer(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест успешного доступа для работодателя"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_employee_selected_courses_404_for_wrong_organization(
        self, client, test_employer_user
    ):
        """Тест - сотрудник из другой организации не доступен"""
        # Создаём другую организацию
        other_org = Organization.objects.create(
            inn="999999999999",
            kpp="999999999",
            ogrn="999999999999999",
            full_name="Другая организация",
            short_name="Другая ООО",
            address_raw="г. Другой",
            status="ACTIVE",
        )
        # Создаём сотрудника в другой организации
        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="pass123",
            user_type="employee",
            organization=other_org,
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_selected_courses", args=[other_employee.id])
        response = client.get(url)
        assert response.status_code == 404

    def test_employee_selected_courses_displays_courses(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест отображения выбранных курсов сотрудника"""
        # Создаём выбранные курсы
        courses = []
        for i in range(3):
            course = Course.objects.create(
                title=f"Курс {i}",
                organization=test_employee_user.organization,
                url=f"https://test.com/course{i}",
                is_deleted=False,
            )
            selected = SelectedCourse.objects.create(
                user=test_employee_user,
                course=course,
            )
            courses.append((course, selected))

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Курс 0" in content
        assert "Курс 1" in content
        assert "Курс 2" in content
        assert "Кнопка удалить" not in content  # Проверяем, что нет кнопки удаления

    def test_employee_selected_courses_shows_approval_status(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест отображения статуса одобрения курсов"""
        from apps.recommendations.models import ApprovedSelectedCourse

        # Создаём курс
        course = Course.objects.create(
            title="Курс с одобрением",
            organization=test_employee_user.organization,
            url="https://test.com/approved",
            is_deleted=False,
        )
        selected = SelectedCourse.objects.create(
            user=test_employee_user,
            course=course,
        )

        # Создаём одобрение
        ApprovedSelectedCourse.objects.create(
            selected_course=selected,
            status="approved",
            approved_by=test_employer_user,
            approved_at=timezone.now(),
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Одобрено" in content

    def test_employee_selected_courses_shows_approval_buttons(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест отображения кнопок одобрения/отклонения для работодателя"""
        # Создаём курс
        course = Course.objects.create(
            title="Курс для одобрения",
            organization=test_employee_user.organization,
            url="https://test.com/approve",
            is_deleted=False,
        )
        selected = SelectedCourse.objects.create(
            user=test_employee_user,
            course=course,
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Одобрить" in content
        assert "Отклонить" in content

    def test_employee_selected_courses_hides_approval_buttons_for_approved(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест - кнопки одобрения/отклонения скрыты если уже одобрено"""
        from apps.recommendations.models import ApprovedSelectedCourse

        # Создаём курс
        course = Course.objects.create(
            title="Уже одобренный курс",
            organization=test_employee_user.organization,
            url="https://test.com/already_approved",
            is_deleted=False,
        )
        selected = SelectedCourse.objects.create(
            user=test_employee_user,
            course=course,
        )

        # Создаём одобрение
        ApprovedSelectedCourse.objects.create(
            selected_course=selected,
            status="approved",
            approved_by=test_employer_user,
            approved_at=timezone.now(),
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Кнопка "Одобрить" должна быть disabled или скрыта
        assert "disabled" in content or "Одобрено" in content

    def test_employee_selected_courses_empty(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест когда у сотрудника нет выбранных курсов"""
        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "нет выбранных курсов" in content.lower() or "0" in content

    def test_employee_selected_courses_prefetches_approval(
        self, client, test_employer_user, test_employee_user
    ):
        """Тест - проверка что prefetch_related('approval') работает"""
        from apps.recommendations.models import ApprovedSelectedCourse

        # Создаём курсы и одобрения
        for i in range(3):
            course = Course.objects.create(
                title=f"Курс {i}",
                organization=test_employee_user.organization,
                url=f"https://test.com/course{i}",
                is_deleted=False,
            )
            selected = SelectedCourse.objects.create(
                user=test_employee_user,
                course=course,
            )
            ApprovedSelectedCourse.objects.create(
                selected_course=selected,
                status="approved" if i % 2 == 0 else "pending",
                approved_by=test_employer_user,
                approved_at=timezone.now(),
            )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse(
            "accounts:employee_selected_courses", args=[test_employee_user.id]
        )
        response = client.get(url)

        assert response.status_code == 200
        # Проверяем, что в контексте есть selected_courses с approval
        selected_courses = response.context["selected_courses"]
        for item in selected_courses:
            assert hasattr(item, "approval")


@pytest.mark.django_db
class TestOrganizationEmployeeCountProperty:
    """Тесты для свойства employee_count в модели Organization"""

    def test_employee_count_property(self, test_organization):
        """Тест подсчёта количества сотрудников"""
        for i in range(5):
            emp = User.objects.create_user(
                username=f"count_emp_{i}",
                email=f"count{i}@test.com",
                password="pass123",
                user_type="employee",
                organization=test_organization,
            )
            EmployeeProfile.objects.create(
                user=emp,
                snils=f"{i:03d}-456-789 01",
                organization=test_organization,
                position="Сотрудник",
                position_level="specialist",
            )

        assert test_organization.employee_count == 5

    def test_employee_count_only_counts_active_employees(self, test_organization):
        """Тест - считаются только активные сотрудники"""
        emp = User.objects.create_user(
            username="inactive_emp",
            email="inactive@test.com",
            password="pass123",
            user_type="employee",
            is_active=False,
            organization=test_organization,
        )
        EmployeeProfile.objects.create(
            user=emp,
            snils="999-999-999 99",
            organization=test_organization,
            position="Неактивный",
            position_level="specialist",
        )

        assert test_organization.employee_count == 0

    def test_employee_count_ignores_non_employee_users(
        self, test_organization, test_employer_user
    ):
        """Тест - не считаются пользователи других типов"""
        assert test_organization.employee_count == 0


@pytest.mark.django_db
class TestOrganizationActiveCoursesCountProperty:
    """Тесты для свойства active_courses_count в модели Organization"""

    def test_active_courses_count_property(self, test_organization, test_course):
        """Тест подсчёта активных курсов"""
        assert test_organization.active_courses_count == 1

    def test_active_courses_count_ignores_deleted(self, test_organization):
        """Тест - удалённые курсы не считаются"""
        course1 = Course.objects.create(
            title="Активный курс",
            organization=test_organization,
            url="https://test.com/active",
            is_deleted=False,
        )
        course2 = Course.objects.create(
            title="Удалённый курс",
            organization=test_organization,
            url="https://test.com/deleted",
            is_deleted=True,
        )
        assert test_organization.active_courses_count == 1


@pytest.mark.django_db
class TestEmployeeRegisterUnemployedView:
    """Тесты регистрации безработного"""

    def test_register_unemployed_success(self, client):
        """Тест успешной регистрации безработного"""
        url = reverse("accounts:employee_register")
        data = {
            "username": "unemployed_new",
            "email": "unemployed_new@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Сидоров",
            "first_name": "Сидор",
            "patronymic": "Сидорович",
            "snils": "111-222-333 44",
            "is_unemployed": "on",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("home")

        user = User.objects.get(username="unemployed_new")
        assert user.organization is None

        profile = user.employee_profile
        assert profile.is_unemployed is True
        assert profile.organization is None
        assert profile.position == "Безработный"
        assert profile.position_level is None

    def test_register_unemployed_svo_success(self, client):
        """Тест регистрации безработного участника СВО"""
        url = reverse("accounts:employee_register")
        data = {
            "username": "unemployed_svo_new",
            "email": "unemployed_svo_new@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Петров",
            "first_name": "Петр",
            "snils": "222-333-444 55",
            "is_unemployed": "on",
            "is_svo_participant": "on",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        user = User.objects.get(username="unemployed_svo_new")
        profile = user.employee_profile
        assert profile.is_unemployed is True
        assert profile.is_svo_participant is True
        assert profile.organization is None

    def test_register_working_svo_success(self, client, test_organization):
        """Тест регистрации работающего участника СВО"""
        url = reverse("accounts:employee_register")
        data = {
            "username": "working_svo_new",
            "email": "working_svo_new@test.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "last_name": "Иванов",
            "first_name": "Иван",
            "snils": "333-444-555 66",
            "organization": test_organization.id,
            "position": "Инженер",
            "position_level": "specialist",
            "is_svo_participant": "on",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        user = User.objects.get(username="working_svo_new")
        profile = user.employee_profile
        assert profile.is_unemployed is False
        assert profile.is_svo_participant is True
        assert profile.organization == test_organization


@pytest.mark.django_db
class TestEmployeeProfileUnemployedView:
    """Тесты редактирования профиля безработного"""

    def test_set_unemployed_via_profile(
        self, client, test_employee_user, test_organization
    ):
        """Тест: работник становится безработным"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "is_unemployed": "on",
            "position": "Инженер",
            "position_level": "specialist",
            "organization_id": test_organization.id,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        profile.refresh_from_db()
        assert profile.is_unemployed is True
        assert profile.organization is None
        assert profile.position == "Безработный"
        assert profile.position_level is None

    def test_unset_unemployed_via_profile(
        self, client, test_employee_user, test_organization
    ):
        """Тест: работник снова становится работающим"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
            "organization_id": test_organization.id,
        }
        response = client.post(url, data)
        assert response.status_code == 302

        profile.refresh_from_db()
        assert profile.is_unemployed is False
        assert profile.organization == test_organization
        assert profile.position == "Инженер"

    def test_toggle_svo_via_profile(
        self, client, test_employee_user, test_organization
    ):
        """Тест переключения флага СВО"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            organization=test_organization,
            position="Инженер",
            position_level="specialist",
        )
        client.login(username=test_employee_user.username, password="testpass123")
        url = reverse("accounts:employee_profile")
        data = {
            "last_name": "Иванов",
            "first_name": "Иван",
            "patronymic": "Иванович",
            "birthday": "1990-01-01",
            "snils": "123-456-789 01",
            "email": "test@test.com",
            "position": "Инженер",
            "position_level": "specialist",
            "organization_id": test_organization.id,
            "is_svo_participant": "on",
        }
        response = client.post(url, data)
        assert response.status_code == 302

        profile.refresh_from_db()
        assert profile.is_svo_participant is True
        assert profile.is_unemployed is False


@pytest.mark.django_db
class TestEmployeeListUnemployedFilter:
    """Тесты: безработные не попадают в список сотрудников организации"""

    def test_unemployed_not_in_employee_list(
        self, client, test_employer_user, test_employee_unemployed_user
    ):
        """Безработный (organization=None) не должен быть в списке"""
        EmployeeProfile.objects.create(
            user=test_employee_unemployed_user,
            snils="555-666-777 88",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )

        client.login(username=test_employer_user.username, password="testpass123")
        url = reverse("accounts:employee_list")
        response = client.get(url)

        assert response.status_code == 200
        employees = response.context["employees"]
        employee_ids = [emp.id for emp in employees]
        assert test_employee_unemployed_user.id not in employee_ids


@pytest.mark.django_db
class TestOrganizationEmployeeCountUnemployed:
    """Тесты: безработные не считаются в employee_count организации"""

    def test_unemployed_not_counted(
        self, test_organization, test_employee_unemployed_user
    ):
        """Безработный не входит в employee_count"""
        EmployeeProfile.objects.create(
            user=test_employee_unemployed_user,
            snils="555-666-777 88",
            organization=None,
            position="Безработный",
            position_level=None,
            is_unemployed=True,
        )
        # Никаких сотрудников в организации
        assert test_organization.employee_count == 0
