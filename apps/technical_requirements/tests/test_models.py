import pytest
from django.db import IntegrityError

from apps.technical_requirements.models import Question, TechnicalRequirement

pytestmark = pytest.mark.django_db


class TestQuestionModel:
    """Тесты для модели Question"""

    def test_creation(self, question_text):
        """Тест создания вопроса"""
        assert question_text.order == 1
        assert question_text.text == "Опишите вашу проблему"
        assert question_text.question_type == "text"
        assert question_text.is_required is True
        assert question_text.is_active is True
        assert question_text.placeholder == "Введите текст..."
        assert question_text.help_text == "Помощь по вопросу"
        assert str(question_text) == "1. Опишите вашу проблему"

    def test_str_method(self, question_text):
        """Тест строкового представления"""
        text = str(question_text)
        assert "1. Опишите вашу проблему" in text

    def test_ordering(self):
        """Тест сортировки по порядку"""
        q1 = Question.objects.create(
            order=1, text="Первый вопрос", question_type="text"
        )
        q2 = Question.objects.create(
            order=2, text="Второй вопрос", question_type="text"
        )
        q3 = Question.objects.create(
            order=3, text="Третий вопрос", question_type="text"
        )

        questions = Question.objects.all()
        assert questions[0].order == 1
        assert questions[1].order == 2
        assert questions[2].order == 3

    def test_unique_order(self):
        """Тест уникальности порядка"""
        Question.objects.create(order=1, text="Первый вопрос", question_type="text")

        with pytest.raises(IntegrityError):
            Question.objects.create(order=1, text="Дубликат", question_type="text")

    def test_question_types(self, question_text, question_choice, question_boolean):
        """Тест разных типов вопросов"""
        assert question_text.question_type == "text"
        assert question_choice.question_type == "choice"
        assert question_boolean.question_type == "boolean"

    def test_question_options(self, question_choice):
        """Тест вариантов ответов"""
        assert question_choice.options == [
            "Автоматизация",
            "Внедрение ИИ",
            "Свой вариант",
        ]

    def test_depends_on_relationship(self, question_boolean, question_depends_on):
        """Тест зависимости вопросов"""
        assert question_depends_on.depends_on == question_boolean
        assert question_depends_on.depends_value == "True"

    def test_inactive_question(self, question_inactive):
        """Тест неактивного вопроса"""
        assert question_inactive.is_active is False


class TestTechnicalRequirementModel:
    """Тесты для модели TechnicalRequirement"""

    def test_creation(self, technical_requirement, employer_user, university_user):
        """Тест создания технического задания"""
        assert technical_requirement.employer == employer_user
        assert technical_requirement.status == "sent"
        assert technical_requirement.universities.count() == 1
        assert (
            technical_requirement.universities.first() == university_user.organization
        )
        assert technical_requirement.created_at is not None

    def test_str_method(self, technical_requirement, employer_user):
        """Тест строкового представления"""
        expected = f"ТЗ #{technical_requirement.id} от {employer_user.get_full_name()}"
        assert str(technical_requirement) == expected

    def test_universities_count_property(
        self, technical_requirement, university_user, another_university_user
    ):
        """Тест свойства universities_count"""
        assert technical_requirement.universities_count == 1

        # Добавляем еще один ВУЗ
        technical_requirement.universities.add(another_university_user.organization)
        assert technical_requirement.universities_count == 2

    def test_get_answer(self, technical_requirement, question_text):
        """Тест получения ответа на вопрос"""
        answer = technical_requirement.get_answer(question_text.id)
        assert answer == "Тестовый ответ"

    def test_get_answer_not_found(self, technical_requirement, question_choice):
        """Тест получения несуществующего ответа"""
        answer = technical_requirement.get_answer(question_choice.id)
        assert answer == ""

    def test_answers_json_field(self, technical_requirement, question_text):
        """Тест JSON поля answers"""
        answers = technical_requirement.answers
        assert isinstance(answers, dict)
        assert str(question_text.id) in answers
        assert answers[str(question_text.id)] == "Тестовый ответ"

    def test_answers_json_field_can_store_complex_data(self, employer_user):
        """Тест хранения сложных данных в JSON поле"""
        requirement = TechnicalRequirement.objects.create(
            employer=employer_user,
            answers={
                "1": "Текстовый ответ",
                "2": ["Вариант 1", "Вариант 2"],
                "3": True,
                "4": 42,
            },
        )
        requirement.refresh_from_db()
        assert requirement.answers["1"] == "Текстовый ответ"
        assert requirement.answers["2"] == ["Вариант 1", "Вариант 2"]
        assert requirement.answers["3"] is True
        assert requirement.answers["4"] == 42

    def test_status_choices(self, employer_user):
        """Тест статусов"""
        for status in ["draft", "sent", "in_development", "completed", "rejected"]:
            requirement = TechnicalRequirement.objects.create(
                employer=employer_user,
                answers={},
                status=status,
            )
            assert requirement.status == status

    def test_default_status(self, employer_user):
        """Тест статуса по умолчанию"""
        requirement = TechnicalRequirement.objects.create(
            employer=employer_user,
            answers={},
        )
        assert requirement.status == "draft"

    def test_ordering(self, employer_user):
        """Тест сортировки (новые сверху)"""
        req1 = TechnicalRequirement.objects.create(
            employer=employer_user,
            answers={},
            status="draft",
        )
        req2 = TechnicalRequirement.objects.create(
            employer=employer_user,
            answers={},
            status="draft",
        )
        # Должны быть в порядке убывания created_at
        requirements = TechnicalRequirement.objects.all()
        assert requirements[0].created_at >= requirements[1].created_at

    def test_employer_related_name(self, employer_user, technical_requirement):
        """Тест related_name для работодателя"""
        assert employer_user.technical_requirements.count() == 1
        assert employer_user.technical_requirements.first() == technical_requirement

    def test_universities_many_to_many(
        self, technical_requirement, university_user, another_university_user
    ):
        """Тест many-to-many связи с ВУЗами"""
        # Добавляем второй ВУЗ
        technical_requirement.universities.add(another_university_user.organization)
        assert technical_requirement.universities.count() == 2

        # Проверяем обратную связь
        assert university_user.organization.received_requirements.count() == 1
        assert another_university_user.organization.received_requirements.count() == 1

    def test_delete_employer_cascade(self, employer_user, technical_requirement):
        """Тест каскадного удаления при удалении работодателя"""
        employer_id = employer_user.id
        requirement_id = technical_requirement.id

        # Удаляем работодателя
        employer_user.delete()

        # Техническое задание должно удалиться каскадно
        assert TechnicalRequirement.objects.filter(id=requirement_id).count() == 0
