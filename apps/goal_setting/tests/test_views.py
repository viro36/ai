import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from apps.goal_setting.models import GoalSettingResponse, QuestionOption

pytestmark = pytest.mark.django_db


class TestGoalSettingView:
    """Тесты для представления goal_setting_view"""

    def test_view_requires_login(self, client):
        """Тест: страница требует авторизации"""
        url = reverse("goal_setting:goal_setting")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_view_get_authenticated(
        self,
        auth_client,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: GET запрос для авторизованного пользователя"""
        url = reverse("goal_setting:goal_setting")
        response = auth_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert "questions" in response.context
        assert "total_questions" in response.context
        assert "progress" in response.context
        assert response.context["total_questions"] == 4
        assert response.context["progress"] == 0

    def test_view_get_with_existing_responses(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
    ):
        """Тест: GET запрос с уже существующими ответами"""
        # Создаём ответ на первый вопрос
        GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_option=test_question_options[0],
        )

        url = reverse("goal_setting:goal_setting")
        response = auth_client.get(url)

        assert response.status_code == 200
        # Прогресс должен быть 1/4 = 25%
        assert response.context["progress"] == 25

    def test_view_post_valid_data(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: POST запрос с валидными данными"""
        url = reverse("goal_setting:goal_setting")
        data = {
            "question_1": "python",
            "question_2": "Я работаю с Python уже 5 лет",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        response = auth_client.post(url, data)

        # Проверяем редирект на главную
        assert response.status_code == 302
        assert response.url == reverse("home")

        # Проверяем сообщение об успехе
        response_follow = auth_client.post(url, data, follow=True)
        messages = list(get_messages(response_follow.wsgi_request))
        assert any("Целеполагание успешно сохранено" in str(msg) for msg in messages)

        # Проверяем, что ответы сохранились
        responses = GoalSettingResponse.objects.filter(user=test_user)
        assert responses.count() == 4

        # Проверяем, что ответ на множественный выбор сохранился как строка с запятыми
        multiple_response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_multiple_choice
        )
        assert multiple_response.answer_text == "python,javascript"

    def test_view_post_valid_data_with_custom_option(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: POST запрос с выбором 'Свой вариант'"""
        url = reverse("goal_setting:goal_setting")
        data = {
            "question_1": "custom",
            "question_1_custom": "Мой любимый язык - Ruby",
            "question_2": "Я работаю с Ruby уже 3 года",
            "question_3": ["ruby", "rails"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        response = auth_client.post(url, data)

        assert response.status_code == 302
        assert response.url == reverse("home")

        # Проверяем сохранение кастомного ответа
        response_obj = GoalSettingResponse.objects.get(
            user=test_user,
            question=test_question_choice,
        )
        assert response_obj.answer_text == "Мой любимый язык - Ruby"
        # Проверяем, что создана кастомная опция (value = custom_{question.id})
        custom_option = QuestionOption.objects.get(
            question=test_question_choice, value=f"custom_{test_question_choice.id}"
        )
        assert response_obj.answer_option == custom_option
        assert custom_option.is_custom is True
        assert custom_option.label == "Мой любимый язык - Ruby"

    def test_view_post_invalid_data(
        self,
        auth_client,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: POST запрос с невалидными данными"""
        url = reverse("goal_setting:goal_setting")
        # Отправляем пустые данные (все поля обязательные)
        data = {}
        response = auth_client.post(url, data)

        # Должен вернуться на страницу с формой (статус 200)
        assert response.status_code == 200
        # Проверяем, что форма содержит ошибки
        assert response.context["form"].errors

        # Проверяем сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        assert any("исправьте ошибки" in str(msg) for msg in messages)

    def test_view_post_required_fields_missing(
        self,
        auth_client,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: POST запрос с пропущенными обязательными полями"""
        url = reverse("goal_setting:goal_setting")
        # Отправляем только часть данных
        data = {
            "question_1": "python",
            # question_2 пропущен
            # question_3 пропущен
            # question_4 пропущен
        }
        response = auth_client.post(url, data)

        # Должен вернуться на страницу с формой (статус 200)
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_view_get_questions_order(
        self,
        auth_client,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: вопросы отображаются в правильном порядке"""
        url = reverse("goal_setting:goal_setting")
        response = auth_client.get(url)

        questions = response.context["questions"]
        assert questions[0].order == 1
        assert questions[0].text == "Какой ваш любимый язык программирования?"
        assert questions[1].order == 2
        assert questions[1].text == "Опишите ваш опыт работы"
        assert questions[2].order == 3
        assert questions[2].text == "Какие технологии вы используете?"
        assert questions[3].order == 4
        assert questions[3].text == "Укажите желаемый период обучения"

    def test_view_progress_calculation(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: правильный расчёт прогресса"""
        url = reverse("goal_setting:goal_setting")

        # Создаём 2 ответа из 4
        questions = [
            test_question_choice,
            test_question_text,
            test_question_multiple_choice,
            test_question_date_range,
        ]
        for question in questions[:2]:
            GoalSettingResponse.objects.create(
                user=test_user,
                question=question,
                answer_text="Тестовый ответ",
            )

        response = auth_client.get(url)
        assert response.context["progress"] == 50

    def test_view_progress_100_percent(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
    ):
        """Тест: прогресс 100% когда все вопросы отвечены"""
        questions = [
            test_question_choice,
            test_question_text,
            test_question_multiple_choice,
            test_question_date_range,
        ]
        for question in questions:
            GoalSettingResponse.objects.create(
                user=test_user,
                question=question,
                answer_text="Тестовый ответ",
            )

        url = reverse("goal_setting:goal_setting")
        response = auth_client.get(url)
        assert response.context["progress"] == 100

    def test_view_post_clears_old_responses(
        self,
        auth_client,
        test_user,
        test_question_choice,
        test_question_text,
        test_question_multiple_choice,
        test_question_date_range,
        test_question_options,
        test_question_multiple_choice_options,
    ):
        """Тест: при отправке формы старые ответы перезаписываются"""
        # Создаём старый ответ на первый вопрос
        GoalSettingResponse.objects.create(
            user=test_user,
            question=test_question_choice,
            answer_text="Старый ответ",
        )
        # Создаём ответы на остальные вопросы, чтобы всего было 4
        questions = [
            test_question_text,
            test_question_multiple_choice,
            test_question_date_range,
        ]
        for question in questions:
            GoalSettingResponse.objects.create(
                user=test_user,
                question=question,
                answer_text="Старый ответ",
            )
        assert GoalSettingResponse.objects.filter(user=test_user).count() == 4

        # Отправляем новую форму
        url = reverse("goal_setting:goal_setting")
        data = {
            "question_1": "python",
            "question_2": "Новый ответ на текст",
            "question_3": ["python", "javascript"],
            "question_4_start": "2026-09-01",
            "question_4_end": "2026-12-31",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 302

        # Проверяем, что старые ответы удалены, созданы новые
        responses = GoalSettingResponse.objects.filter(user=test_user)
        assert responses.count() == 4

        # Проверяем что у первого вопроса теперь другой ответ и текст очищен
        first_response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_choice
        )
        assert first_response.answer_text is None
        assert first_response.answer_option is not None
        assert first_response.answer_option.value == "python"

        # Проверяем, что остальные ответы тоже обновились
        text_response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_text
        )
        assert text_response.answer_text == "Новый ответ на текст"

        # Проверяем, что на множественный выбор сохранился новый ответ
        multiple_response = GoalSettingResponse.objects.get(
            user=test_user, question=test_question_multiple_choice
        )
        assert multiple_response.answer_text == "python,javascript"
        assert multiple_response.answer_option is None
