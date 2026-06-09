import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.surveys.models import (
    SurveyBlock,
    SurveyQuestion,
    SurveySession,
    UserSurveyResponse,
)

User = get_user_model()


# ============================================================
# Тесты для survey_list
# ============================================================


@pytest.mark.django_db
class TestSurveyListView:
    """Тесты для отображения списка опросов"""

    def test_survey_list_requires_login(self, client):
        """Тест: требуется авторизация"""
        url = reverse("surveys:survey_list")
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_survey_list_authenticated(self, client, user, survey_category):
        """Тест: авторизованный пользователь видит опросы"""
        client.force_login(user)
        url = reverse("surveys:survey_list")
        response = client.get(url)

        assert response.status_code == 200
        assert "categories" in response.context
        assert survey_category in response.context["categories"]

    def test_survey_list_only_active(
        self, client, user, survey_category, inactive_category
    ):
        """Тест: показываются только активные опросы"""
        client.force_login(user)
        url = reverse("surveys:survey_list")
        response = client.get(url)

        categories = response.context["categories"]
        assert survey_category in categories
        assert inactive_category not in categories

    def test_survey_list_with_completed_session(
        self, client, user, survey_category, completed_session
    ):
        """Тест: опрос отмечен как пройденный"""
        client.force_login(user)
        url = reverse("surveys:survey_list")
        response = client.get(url)

        category = response.context["categories"][0]
        assert category.has_completed is True
        assert category.attempts_count == 1

    def test_survey_list_with_in_progress(
        self, client, user, survey_category, survey_session
    ):
        """Тест: опрос в процессе"""
        client.force_login(user)
        url = reverse("surveys:survey_list")
        response = client.get(url)

        category = response.context["categories"][0]
        assert category.has_in_progress is True


# ============================================================
# Тесты для survey_start
# ============================================================


@pytest.mark.django_db
class TestSurveyStartView:
    """Тесты для начала опроса"""

    def test_survey_start_requires_login(self, client, survey_category):
        """Тест: требуется авторизация"""
        url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_survey_start_new_session(
        self, client, user, survey_category, survey_block, survey_question
    ):
        """Тест: создание новой сессии"""
        client.force_login(user)

        # Создаём блок и вопрос
        SurveyBlock.objects.create(category=survey_category, title="Блок 1", order=1)
        SurveyQuestion.objects.create(block=survey_block, text="Вопрос 1", q_number=1)

        url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(url)

        # Должен быть редирект на первый вопрос
        assert response.status_code == 302
        assert "/surveys/question/" in response.url

        # Проверяем, что сессия создана
        session = SurveySession.objects.filter(
            user=user, category=survey_category
        ).first()
        assert session is not None
        assert session.attempt == 1
        assert session.status == "in_progress"

    def test_survey_start_continue_in_progress(
        self, client, user, survey_category, survey_session
    ):
        """Тест: продолжение незавершённого опроса"""
        client.force_login(user)

        url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(url)

        # Должен быть редирект на continue
        assert response.status_code == 302
        assert "continue" in response.url

    def test_survey_start_new_attempt_after_completion(
        self,
        client,
        user,
        survey_category,
        completed_session,
        survey_block,
        survey_question,
    ):
        """Тест: новая попытка после завершения"""
        client.force_login(user)

        # Создаём блок и вопрос для нового опроса
        SurveyQuestion.objects.create(block=survey_block, text="Вопрос 1", q_number=1)

        url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(url)

        # Новая сессия с attempt=2
        new_session = SurveySession.objects.filter(
            user=user, category=survey_category, attempt=2
        ).first()
        assert new_session is not None
        assert new_session.status == "in_progress"

    def test_survey_start_inactive_category(self, client, user, inactive_category):
        """Тест: попытка начать неактивный опрос"""
        client.force_login(user)

        url = reverse("surveys:survey_start", args=[inactive_category.id])
        response = client.get(url, follow=True)

        # Должен быть редирект на список опросов
        assert response.status_code == 200
        # Проверяем сообщение
        assert "недоступен" in response.content.decode("utf-8")

    def test_survey_start_no_questions(self, client, user, survey_category):
        """Тест: опрос без вопросов"""
        client.force_login(user)

        url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(url, follow=True)

        messages = list(response.context["messages"])
        assert any("нет вопросов" in str(m.message) for m in messages)


# ============================================================
# Тесты для survey_continue
# ============================================================


@pytest.mark.django_db
class TestSurveyContinueView:
    """Тесты для продолжения опроса"""

    def test_survey_continue_with_session(
        self, client, user, survey_category, survey_session
    ):
        """Тест: продолжение существующей сессии"""
        client.force_login(user)

        url = reverse("surveys:survey_continue", args=[survey_category.id])
        response = client.get(url)

        assert response.status_code == 302

    def test_survey_continue_no_session(self, client, user, survey_category):
        """Тест: попытка продолжить без сессии"""
        client.force_login(user)

        url = reverse("surveys:survey_continue", args=[survey_category.id])
        response = client.get(url, follow=True)

        messages = list(response.context["messages"])
        assert any("Нет незавершённого опроса" in str(m.message) for m in messages)


# ============================================================
# Тесты для survey_question
# ============================================================


@pytest.mark.django_db
class TestSurveyQuestionView:
    """Тесты для отображения вопроса"""

    def test_survey_question_get(
        self,
        client,
        user,
        survey_category,
        survey_block,
        survey_question,
        survey_session,
    ):
        """Тест: GET запрос вопроса"""
        client.force_login(user)

        url = reverse(
            "surveys:survey_question",
            args=[survey_category.id, survey_block.id, survey_question.id],
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "question" in response.context
        assert response.context["question"].text == survey_question.text

    def test_survey_question_post_valid(
        self,
        client,
        user,
        survey_category,
        survey_block,
        survey_question,
        survey_session,
    ):
        """Тест: POST с валидным ответом"""
        client.force_login(user)

        url = reverse(
            "surveys:survey_question",
            args=[survey_category.id, survey_block.id, survey_question.id],
        )
        response = client.post(url, {"score": "4"})

        # Проверяем, что ответ сохранён
        saved_response = UserSurveyResponse.objects.filter(
            user=user, question=survey_question, session=survey_session
        ).first()
        assert saved_response is not None
        assert saved_response.score == 4

        # Редирект на следующий вопрос
        assert response.status_code == 302

    def test_survey_question_post_invalid(
        self,
        client,
        user,
        survey_category,
        survey_block,
        survey_question,
        survey_session,
    ):
        """Тест: POST без выбора ответа"""
        client.force_login(user)

        url = reverse(
            "surveys:survey_question",
            args=[survey_category.id, survey_block.id, survey_question.id],
        )
        response = client.post(url, {}, follow=True)

        messages = list(response.context["messages"])
        assert any("выберите вариант ответа" in str(m.message) for m in messages)

    def test_survey_question_last_question(
        self,
        client,
        user,
        survey_category,
        survey_block,
        survey_question,
        survey_session,
    ):
        """Тест: последний вопрос опроса"""
        client.force_login(user)

        # Создаём один вопрос - он будет последним
        url = reverse(
            "surveys:survey_question",
            args=[survey_category.id, survey_block.id, survey_question.id],
        )
        response = client.post(url, {"score": "4"}, follow=True)

        # Должен быть редирект на результаты
        assert response.status_code == 200
        assert "results" in response.request["PATH_INFO"]


# ============================================================
# Тесты для survey_results
# ============================================================


@pytest.mark.django_db
class TestSurveyResultsView:
    """Тесты для отображения результатов"""

    def test_survey_results_requires_login(self, client, survey_category):
        """Тест: требуется авторизация"""
        url = reverse("surveys:survey_results", args=[survey_category.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_survey_results_no_session(self, client, user, survey_category):
        """Тест: результаты без пройденного опроса"""
        client.force_login(user)

        url = reverse("surveys:survey_results", args=[survey_category.id])
        response = client.get(url, follow=True)

        messages = list(response.context["messages"])
        assert any("ещё не прошли" in str(m.message) for m in messages)

    def test_survey_results_with_session(
        self, client, user, survey_category, completed_session
    ):
        """Тест: отображение результатов"""
        client.force_login(user)

        url = reverse("surveys:survey_results", args=[survey_category.id])
        response = client.get(url)

        assert response.status_code == 200
        assert "current_attempt" in response.context
        assert response.context["current_attempt"] == 1

    def test_survey_results_specific_attempt(
        self, client, user, survey_category, multiple_sessions
    ):
        """Тест: отображение конкретной попытки"""
        client.force_login(user)

        url = reverse("surveys:survey_results_attempt", args=[survey_category.id, 2])
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["current_attempt"] == 2


# ============================================================
# Тесты для survey_results_history
# ============================================================


@pytest.mark.django_db
class TestSurveyHistoryView:
    """Тесты для истории опросов"""

    def test_survey_history_requires_login(self, client, survey_category):
        """Тест: требуется авторизация"""
        url = reverse("surveys:survey_history", args=[survey_category.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_survey_history_empty(self, client, user, survey_category):
        """Тест: история без попыток"""
        client.force_login(user)

        url = reverse("surveys:survey_history", args=[survey_category.id])
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["sessions"].count() == 0

    def test_survey_history_with_sessions(
        self, client, user, survey_category, multiple_sessions
    ):
        """Тест: история с несколькими попытками"""
        client.force_login(user)

        url = reverse("surveys:survey_history", args=[survey_category.id])
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["sessions"].count() == 3


# ============================================================
# Интеграционные тесты для полного цикла
# ============================================================


@pytest.mark.django_db
class TestFullSurveyFlow:
    """Тесты полного цикла прохождения опроса"""

    def test_complete_survey_flow(
        self,
        client,
        user,
        survey_category,
        survey_block,
        multiple_questions,
        global_scale_labels,
    ):
        """Тест полного цикла: старт -> ответы -> результаты"""
        client.force_login(user)

        # 1. Начинаем опрос
        start_url = reverse("surveys:survey_start", args=[survey_category.id])
        response = client.get(start_url)
        assert response.status_code == 302

        # 2. Проходим все вопросы
        questions = SurveyQuestion.objects.filter(block=survey_block).order_by(
            "q_number"
        )
        session = SurveySession.objects.filter(
            user=user, category=survey_category
        ).first()

        for i, question in enumerate(questions, 1):
            url = reverse(
                "surveys:survey_question",
                args=[survey_category.id, survey_block.id, question.id],
            )
            response = client.post(url, {"score": str(i % 5 + 1)})

            if i < len(questions):
                assert response.status_code == 302
            else:
                assert response.status_code == 302

        # 3. Проверяем результаты - обновляем session из базы
        session = SurveySession.objects.get(id=session.id)
        assert session.status == "completed"
        assert session.completed_at is not None

        results_url = reverse("surveys:survey_results", args=[survey_category.id])
        response = client.get(results_url)
        assert response.status_code == 200

    def test_multiple_attempts_flow(
        self,
        client,
        user,
        survey_category,
        survey_block,
        multiple_questions,
        global_scale_labels,
    ):
        """Тест нескольких попыток прохождения"""
        client.force_login(user)

        # Первая попытка - проходим все вопросы
        start_url = reverse("surveys:survey_start", args=[survey_category.id])
        client.get(start_url)

        questions = SurveyQuestion.objects.filter(block=survey_block).order_by(
            "q_number"
        )
        for i, question in enumerate(questions, 1):
            url = reverse(
                "surveys:survey_question",
                args=[survey_category.id, survey_block.id, question.id],
            )
            client.post(url, {"score": "3"})

        # Вторая попытка
        client.get(start_url)

        # Вторая попытка - тоже проходим все вопросы
        for i, question in enumerate(questions, 1):
            url = reverse(
                "surveys:survey_question",
                args=[survey_category.id, survey_block.id, question.id],
            )
            client.post(url, {"score": "4"})

        # Проверяем, что созданы две завершённые попытки
        sessions = SurveySession.objects.filter(
            user=user, category=survey_category, status="completed"
        )
        assert sessions.count() == 2
        assert sessions[0].attempt == 2  # последняя попытка первая
        assert sessions[1].attempt == 1
