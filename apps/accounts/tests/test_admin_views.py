import pytest
from datetime import date
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib.messages import get_messages
from apps.goal_setting.models import GoalSettingResponse, Question
from apps.organizations.models import Organization
from apps.accounts.models import EmployeeProfile, EmployerRegistrationRequest
from apps.recommendations.models import CourseRecommendation, SelectedCourse
from apps.surveys.models import RiasacResult, SurveyCategory, SurveySession
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


@pytest.mark.django_db
class TestEmployeeFullProfileView:
    """Тесты для view employee_full_profile"""

    def _create_profile(self, user, **overrides):
        """Хелпер: создаёт профиль работника с разумными значениями по умолчанию"""
        defaults = {
            "user": user,
            "snils": "123-456-789 01",
            "position": "Безработный",
            "is_unemployed": True,
        }
        defaults.update(overrides)
        return EmployeeProfile.objects.create(**defaults)

    def test_requires_staff(self, client, test_employee_user):
        """Не-админ не может открыть страницу"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = client.get(url)
        # Редирект на логин или 403
        assert response.status_code in [302, 403]

    def test_admin_can_open(self, admin_client, test_employee_user):
        """Админ видит карточку (код 200)"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_admin_sees_expected_blocks(self, admin_client, test_employee_user):
        """На странице присутствуют ключевые блоки"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        content = response.content.decode()

        assert "Статусы готовности" in content
        assert "Пользователь (CustomUser)" in content
        assert "Профиль работника" in content
        assert "Целеполагание" in content
        assert "Опросы" in content
        assert "RIASEC" in content
        assert "Рекомендации курсов" in content
        assert "Выбранные курсы" in content

    def test_404_for_missing_profile(self, admin_client):
        """404 для несуществующего профиля"""
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[999999])
        response = admin_client.get(url)
        assert response.status_code == 404

    def test_context_contains_jazzmin_keys(self, admin_client, test_employee_user, rf):
        """В контексте есть ключи для Jazzmin (available_apps, app_list)"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "available_apps" in response.context
        assert "app_list" in response.context
        assert response.context["is_nav_sidebar_enabled"] is True
        assert response.context["has_permission"] is True

    def test_context_contains_profile_and_user(self, admin_client, test_employee_user):
        """В контексте есть profile и u (пользователь)"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["profile"].id == profile.id
        assert response.context["u"].id == test_employee_user.id

    def test_context_contains_admin_urls(self, admin_client, test_employee_user):
        """В контексте есть ссылки на редактирование пользователя и профиля"""
        profile = self._create_profile(test_employee_user)
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        ctx = response.context

        assert ctx["user_admin_url"] == reverse(
            "admin:users_customuser_change", args=[test_employee_user.id]
        )
        assert ctx["profile_edit_url"] == reverse(
            "admin:accounts_employeeprofile_change", args=[profile.id]
        )


@pytest.mark.django_db
class TestEmployeeFullProfileMissingFields:
    """Проверка блока missing_fields в контексте"""

    def test_missing_birthday(self, admin_client, test_employee_user):
        """Если у пользователя нет birthday — попадает в missing_fields"""
        test_employee_user.birthday = None
        test_employee_user.save()

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        missing = dict(response.context["missing_fields"])
        assert "birthday" in missing

    def test_missing_profile_fields(self, admin_client, test_employee_user):
        """Пустые поля профиля попадают в missing_fields"""
        test_employee_user.birthday = date(1990, 1, 1)
        test_employee_user.save()

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        missing = dict(response.context["missing_fields"])

        assert "gender" in missing
        assert "education_level" in missing
        assert "graduation_year" in missing
        assert "education_institution" in missing
        assert "specialty" in missing
        assert "locality" in missing
        assert "municipality" in missing

    def test_missing_work_fields_for_employed(self, admin_client, test_employee_user):
        """Для работающего обязательны organization, position, position_level"""
        test_employee_user.birthday = date(1990, 1, 1)
        test_employee_user.save()

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="",
            is_unemployed=False,
            organization=None,
            position_level=None,
            gender="M",
            citizenship="Россия",
            education_level="higher",
            graduation_year=2014,
            education_institution="ВГУ",
            specialty="Инженер",
            locality="Воронеж",
            municipality="Воронеж",
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        missing = dict(response.context["missing_fields"])

        assert "organization" in missing
        assert "position" in missing
        assert "position_level" in missing

    def test_no_missing_fields_when_full(
        self, admin_client, test_employee_user, test_organization
    ):
        """Если всё заполнено — missing_fields пуст"""
        test_employee_user.birthday = date(1990, 1, 1)
        test_employee_user.save()

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Инженер",
            position_level="specialist",
            is_unemployed=False,
            organization=test_organization,
            gender="M",
            citizenship="Россия",
            education_level="higher",
            graduation_year=2014,
            education_institution="ВГУ",
            specialty="Инженер",
            locality="Воронеж",
            municipality="Воронеж",
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["missing_fields"] == []
        assert response.context["profile_complete"] is True


@pytest.mark.django_db
class TestEmployeeFullProfileGoalSetting:
    """Проверка блока целеполагания"""

    def test_goal_setting_empty(self, admin_client, test_employee_user):
        """Нет вопросов — total_questions=0, goal_setting_complete=False"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["total_questions"] == 0
        assert response.context["goal_setting_complete"] is False

    def test_goal_setting_complete(self, admin_client, test_employee_user):
        """Все активные вопросы имеют ответ — goal_setting_complete=True"""
        q1 = Question.objects.create(text="Вопрос 1", is_active=True)
        q2 = Question.objects.create(text="Вопрос 2", is_active=True)

        GoalSettingResponse.objects.create(user=test_employee_user, question=q1)
        GoalSettingResponse.objects.create(user=test_employee_user, question=q2)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["total_questions"] == 2
        assert response.context["answered_count"] == 2
        assert response.context["goal_setting_complete"] is True
        assert response.context["unanswered"].count() == 0

    def test_goal_setting_partial(self, admin_client, test_employee_user):
        """Часть вопросов без ответа — unanswered не пуст"""
        q1 = Question.objects.create(text="Вопрос 1", is_active=True)
        q2 = Question.objects.create(text="Вопрос 2", is_active=True)

        GoalSettingResponse.objects.create(user=test_employee_user, question=q1)

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["answered_count"] == 1
        assert response.context["total_questions"] == 2
        assert response.context["goal_setting_complete"] is False
        assert response.context["unanswered"].count() == 1


@pytest.mark.django_db
class TestEmployeeFullProfileSurveys:
    """Проверка блока опросов"""

    def test_no_active_surveys(self, admin_client, test_employee_user):
        """Нет активных опросов — surveys_total=0"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["surveys_total"] == 0
        assert response.context["surveys_completed_count"] == 0

    def test_surveys_summary(self, admin_client, test_employee_user):
        """Опросы в контексте: пройден / не пройден"""
        cat1 = SurveyCategory.objects.create(name="Опрос 1", is_active=True)
        cat2 = SurveyCategory.objects.create(name="Опрос 2", is_active=True)

        # Пройдем только первый
        SurveySession.objects.create(
            user=test_employee_user,
            category=cat1,
            status="completed",
            attempt=1,
            completed_at=timezone.now(),
        )

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)

        summary = response.context["surveys_summary"]
        assert len(summary) == 2
        assert response.context["surveys_total"] == 2
        assert response.context["surveys_completed_count"] == 1

        by_cat = {s["category"].id: s for s in summary}
        assert by_cat[cat1.id]["completed"] is True
        assert by_cat[cat2.id]["completed"] is False


@pytest.mark.django_db
class TestEmployeeFullProfileRiasec:
    """Проверка блока RIASEC"""

    def test_no_riasec(self, admin_client, test_employee_user):
        """RIASEC не пройден — riasac=None, riasec_scores={}"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["riasac"] is None
        assert response.context["riasec_scores"] == {}

    def test_riasec_present(self, admin_client, test_employee_user):
        """RIASEC есть — в контексте riasac и riasec_scores"""
        cat = SurveyCategory.objects.create(name="Холланд", is_active=True)
        session = SurveySession.objects.create(
            user=test_employee_user,
            category=cat,
            status="completed",
            attempt=1,
            completed_at=timezone.now(),
        )
        RiasacResult.objects.create(
            session=session,
            r_score=10,
            i_score=20,
            a_score=30,
            s_score=40,
            e_score=50,
            c_score=5,
            career_code="SIA",
            dominant_types="S, I, A",
        )

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)

        assert response.context["riasac"] is not None
        assert response.context["riasac"].career_code == "SIA"
        scores = response.context["riasec_scores"]
        assert scores["R"] == 10
        assert scores["I"] == 20
        assert scores["A"] == 30
        assert scores["S"] == 40
        assert scores["E"] == 50
        assert scores["C"] == 5


@pytest.mark.django_db
class TestEmployeeFullProfileRecommendationsAndCourses:
    """Проверка блоков рекомендаций и выбранных курсов"""

    def test_empty_recommendations_and_courses(self, admin_client, test_employee_user):
        """Пустые рекомендации и выбранные курсы"""
        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["recommendations_count"] == 0
        assert response.context["selected_courses_count"] == 0

    def test_recommendations_and_courses(
        self,
        admin_client,
        test_employee_user,
        test_course,
    ):
        """Есть рекомендации и выбранные курсы"""
        CourseRecommendation.objects.create(
            user=test_employee_user,
            course=test_course,
            reason="Подходит по профилю",
            relevance_score=0.75,
            order=1,
        )
        SelectedCourse.objects.create(
            user=test_employee_user,
            course=test_course,
        )

        profile = EmployeeProfile.objects.create(
            user=test_employee_user,
            snils="123-456-789 01",
            position="Безработный",
            is_unemployed=True,
        )
        url = reverse("admin:accounts_employeeprofile_full_profile", args=[profile.id])
        response = admin_client.get(url)
        assert response.context["recommendations_count"] == 1
        assert response.context["selected_courses_count"] == 1
