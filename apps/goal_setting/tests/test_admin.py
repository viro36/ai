import pytest
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from apps.goal_setting.admin import (
    QuestionAdmin,
    QuestionOptionAdmin,
    GoalSettingResponseAdmin,
    QuestionOptionInline,
)
from apps.goal_setting.models import Question, QuestionOption, GoalSettingResponse

pytestmark = pytest.mark.django_db


class TestAdminAccess:
    """Тесты доступа к админке"""

    def test_admin_index_requires_login(self, client):
        url = reverse("admin:index")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_admin_index_accessible_for_admin(self, admin_client):
        url = reverse("admin:index")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestQuestionAdmin:
    """Тесты для QuestionAdmin"""

    def test_list_display(self):
        admin = QuestionAdmin(Question, AdminSite())
        assert admin.list_display == (
            "order",
            "text",
            "question_type",
            "is_required",
            "is_active",
        )

    def test_list_filter(self):
        admin = QuestionAdmin(Question, AdminSite())
        assert admin.list_filter == ("question_type", "is_required", "is_active")

    def test_search_fields(self):
        admin = QuestionAdmin(Question, AdminSite())
        assert admin.search_fields == ("text",)

    def test_ordering(self):
        admin = QuestionAdmin(Question, AdminSite())
        assert admin.ordering == ("order",)

    def test_inlines(self):
        admin = QuestionAdmin(Question, AdminSite())
        assert admin.inlines == [QuestionOptionInline]

    def test_fieldsets(self):
        admin = QuestionAdmin(Question, AdminSite())
        fieldsets = admin.fieldsets
        assert len(fieldsets) == 2
        assert fieldsets[0][0] == "Основная информация"
        assert "text" in fieldsets[0][1]["fields"]
        assert "question_type" in fieldsets[0][1]["fields"]
        assert fieldsets[1][0] == "Настройки"
        assert "is_required" in fieldsets[1][1]["fields"]
        assert "is_active" in fieldsets[1][1]["fields"]
        assert "has_custom_option" in fieldsets[1][1]["fields"]

    def test_question_admin_changelist(self, admin_client, test_question_choice):
        url = reverse("admin:goal_setting_question_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert test_question_choice.text in response.content.decode()

    def test_question_admin_add_page(self, admin_client):
        url = reverse("admin:goal_setting_question_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_question_admin_change_page(self, admin_client, test_question_choice):
        url = reverse(
            "admin:goal_setting_question_change", args=[test_question_choice.id]
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        assert test_question_choice.text in response.content.decode()

    def test_question_admin_search(self, admin_client, test_question_choice):
        url = reverse("admin:goal_setting_question_changelist")
        response = admin_client.get(url, {"q": test_question_choice.text[:10]})
        assert response.status_code == 200
        assert test_question_choice.text in response.content.decode()

    def test_question_admin_filter(self, admin_client, test_question_choice):
        url = reverse("admin:goal_setting_question_changelist")
        response = admin_client.get(url, {"question_type": "choice"})
        assert response.status_code == 200
        assert test_question_choice.text in response.content.decode()


class TestQuestionOptionAdmin:
    """Тесты для QuestionOptionAdmin"""

    def test_list_display(self):
        admin = QuestionOptionAdmin(QuestionOption, AdminSite())
        assert admin.list_display == (
            "question",
            "label",
            "value",
            "is_custom",
            "order",
        )

    def test_list_filter(self):
        admin = QuestionOptionAdmin(QuestionOption, AdminSite())
        assert admin.list_filter == ("question", "is_custom")

    def test_search_fields(self):
        admin = QuestionOptionAdmin(QuestionOption, AdminSite())
        assert admin.search_fields == ("label", "value")

    def test_question_option_admin_changelist(
        self, admin_client, test_question_options
    ):
        url = reverse("admin:goal_setting_questionoption_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Python" in content

    def test_question_option_admin_add_page(self, admin_client, test_question_choice):
        url = reverse("admin:goal_setting_questionoption_add")
        response = admin_client.get(url)
        assert response.status_code == 200


class TestGoalSettingResponseAdmin:
    """Тесты для GoalSettingResponseAdmin"""

    def test_list_display(self):
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        assert admin.list_display == (
            "user",
            "question",
            "get_answer_preview",
            "updated_at",
        )

    def test_list_filter(self):
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        assert admin.list_filter == ("question",)

    def test_search_fields(self):
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        assert admin.search_fields == ("user__username", "user__email", "answer_text")

    def test_readonly_fields(self):
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        assert admin.readonly_fields == ("updated_at",)

    def test_get_answer_preview_with_option(self, test_goal_setting_response):
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        preview = admin.get_answer_preview(test_goal_setting_response)
        assert preview == "Python"

    def test_get_answer_preview_with_text(self, test_user, test_question_text):
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_text,
            answer_text="Длинный текст ответа" * 10,
        )
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        preview = admin.get_answer_preview(response)
        # Длина текста: 50 символов + '...'
        assert len(preview) == 53
        assert preview.endswith("...")

    def test_get_answer_preview_with_short_text(self, test_user, test_question_text):
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_text,
            answer_text="Короткий ответ",
        )
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        preview = admin.get_answer_preview(response)
        assert preview == "Короткий ответ"
        assert "..." not in preview

    def test_get_answer_preview_with_date_range(
        self, test_user, test_question_date_range
    ):
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_date_range,
            answer_date_start="2026-09-01",
            answer_date_end="2026-12-31",
        )
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        preview = admin.get_answer_preview(response)
        assert preview == "2026-09-01 - 2026-12-31"

    def test_get_answer_preview_empty(self, test_user, test_question_choice):
        response = GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
        )
        admin = GoalSettingResponseAdmin(GoalSettingResponse, AdminSite())
        preview = admin.get_answer_preview(response)
        assert preview == "-"

    def test_goal_setting_response_admin_changelist(
        self, admin_client, test_goal_setting_response
    ):
        url = reverse("admin:goal_setting_goalsettingresponse_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        # В админке отображается строковое представление пользователя: "Тестов Пользователь"
        assert "Тестов Пользователь" in content

    def test_goal_setting_response_admin_add_page(self, admin_client):
        url = reverse("admin:goal_setting_goalsettingresponse_add")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_goal_setting_response_admin_change_page(
        self, admin_client, test_goal_setting_response
    ):
        url = reverse(
            "admin:goal_setting_goalsettingresponse_change",
            args=[test_goal_setting_response.id],
        )
        response = admin_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Тестов Пользователь" in content
