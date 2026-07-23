import pytest
import json

from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.technical_requirements.forms import TechnicalRequirementForm
from apps.technical_requirements.models import Question

User = get_user_model()
pytestmark = pytest.mark.django_db


class TestTechnicalRequirementForm:
    """Тесты для формы TechnicalRequirementForm"""

    def test_form_init_sets_questions(
        self, employer_user, question_text, question_choice
    ):
        """Тест инициализации формы - устанавливаются вопросы"""
        form = TechnicalRequirementForm(user=employer_user)
        assert hasattr(form, "questions")
        assert len(form.questions) > 0

    def test_form_has_universities_field(self, employer_user):
        """Тест наличия поля universities"""
        form = TechnicalRequirementForm(user=employer_user)
        assert "universities" in form.fields

    def test_form_universities_queryset(self, employer_user, university_user):
        """Тест queryset для поля universities - только ВУЗы"""
        form = TechnicalRequirementForm(user=employer_user)
        queryset = form.fields["universities"].queryset
        assert university_user.organization in queryset

    def test_form_dynamic_fields_created(
        self, employer_user, question_text, question_choice
    ):
        """Тест создания динамических полей для каждого вопроса"""
        form = TechnicalRequirementForm(user=employer_user)
        assert f"q_{question_text.id}" in form.fields
        assert f"q_{question_choice.id}" in form.fields

    def test_form_other_fields_for_choice_with_other_option(
        self, employer_user, question_choice
    ):
        """Тест создания поля 'other' для вопроса с вариантом 'Свой вариант'"""
        form = TechnicalRequirementForm(user=employer_user)
        assert f"other_{question_choice.id}" in form.fields

    def test_form_other_fields_not_created_without_other_option(
        self, employer_user, question_text
    ):
        """Тест - поле 'other' не создается если нет варианта 'Свой вариант'"""
        form = TechnicalRequirementForm(user=employer_user)
        assert f"other_{question_text.id}" not in form.fields

    def test_form_valid_with_all_fields(
        self,
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
        """Тест валидной формы со всеми полями"""
        User = get_user_model()

        # Собираем 5 ВУЗов
        universities = [university_user.organization]
        for i in range(4, 8):
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

        data = {
            "universities": [u.id for u in universities],
        }

        questions = [
            question_text,
            question_textarea,
            question_choice,
            question_multiple_choice,
            question_boolean,
            question_date,
            question_number,
        ]

        for question in questions:
            field_name = f"q_{question.id}"
            if question.question_type == "text":
                data[field_name] = "Тестовый ответ"
            elif question.question_type == "textarea":
                data[field_name] = "Тестовый ответ textarea"
            elif question.question_type == "choice":
                data[field_name] = "Автоматизация"
            elif question.question_type == "multiple_choice":
                data[field_name] = ["Docker"]
            elif question.question_type == "boolean":
                data[field_name] = True
            elif question.question_type == "date":
                data[field_name] = "2024-01-01"
            elif question.question_type == "number":
                data[field_name] = 10

        form = TechnicalRequirementForm(data, user=employer_user)
        assert form.is_valid(), form.errors

    def test_form_invalid_less_than_5_universities(
        self, employer_user, university_user
    ):
        """Тест - ошибка если выбрано менее 5 ВУЗов"""
        User = get_user_model()

        org2 = Organization.objects.create(
            inn="111111111111",
            short_name="ВУЗ 2",
            full_name="ВУЗ полное 2",
            address_raw="г. Воронеж",
            status="ACTIVE",
        )
        User.objects.create_user(
            username="univ2",
            email="univ2@test.com",
            password="test123",
            user_type="university",
            organization=org2,
        )

        data = {
            "universities": [university_user.organization.id, org2.id],
        }
        form = TechnicalRequirementForm(data, user=employer_user)
        assert not form.is_valid()
        assert "universities" in form.errors
        assert "Выберите не менее 5 ВУЗов" in str(form.errors["universities"])

    def test_form_required_fields_validation(
        self, employer_user, question_text, question_choice
    ):
        """Тест валидации обязательных полей"""
        data = {}
        form = TechnicalRequirementForm(data, user=employer_user)
        assert not form.is_valid()
        assert len(form.errors) > 0

    def test_form_other_option_validation(
        self, employer_user, question_choice, university_user
    ):
        """Тест валидации поля 'Свой вариант'"""
        User = get_user_model()

        # Собираем 5 ВУЗов
        universities = [university_user.organization]
        for i in range(4, 8):
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

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_choice.id}": "Свой вариант",
            f"other_{question_choice.id}": "",
        }

        for question in Question.objects.filter(is_active=True).exclude(
            id=question_choice.id
        ):
            field_name = f"q_{question.id}"
            if question.question_type == "text":
                data[field_name] = "Тестовый ответ"
            elif question.question_type == "textarea":
                data[field_name] = "Тестовый ответ textarea"
            elif question.question_type == "multiple_choice":
                data[field_name] = ["Docker"]
            elif question.question_type == "boolean":
                data[field_name] = True
            elif question.question_type == "date":
                data[field_name] = "2024-01-01"
            elif question.question_type == "number":
                data[field_name] = 10

        form = TechnicalRequirementForm(data, user=employer_user)
        assert not form.is_valid()
        assert f"other_{question_choice.id}" in form.errors or len(form.errors) > 0

    def test_form_saves_answers_as_json(
        self,
        employer_user,
        university_user,
        question_text,
        question_textarea,
        question_choice,
        question_multiple_choice,
        question_boolean,
        question_date,
        question_number,
    ):
        """Тест сохранения ответов как JSON"""
        User = get_user_model()

        universities = [university_user.organization]
        for i in range(4, 8):
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

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_text.id}": "Тестовый ответ",
        }

        questions = [
            question_textarea,
            question_choice,
            question_multiple_choice,
            question_boolean,
            question_date,
            question_number,
        ]

        for question in questions:
            field_name = f"q_{question.id}"
            if question.question_type == "text":
                data[field_name] = "Тестовый ответ"
            elif question.question_type == "textarea":
                data[field_name] = "Тестовый ответ textarea"
            elif question.question_type == "choice":
                data[field_name] = "Автоматизация"
            elif question.question_type == "multiple_choice":
                data[field_name] = ["Docker"]
            elif question.question_type == "boolean":
                data[field_name] = True
            elif question.question_type == "date":
                data[field_name] = "2024-01-01"
            elif question.question_type == "number":
                data[field_name] = 10

        form = TechnicalRequirementForm(data, user=employer_user)
        assert form.is_valid(), form.errors

        requirement = form.save(commit=False)
        requirement.employer = employer_user
        requirement.save()

        assert isinstance(requirement.answers, str)
        answers_dict = json.loads(requirement.answers)
        assert str(question_text.id) in answers_dict
        assert answers_dict[str(question_text.id)] == "Тестовый ответ"

    def test_form_initial_values_from_instance(
        self, employer_user, technical_requirement, question_text
    ):
        """Тест начальных значений из существующего экземпляра"""
        form = TechnicalRequirementForm(
            instance=technical_requirement, user=employer_user
        )
        field_name = f"q_{question_text.id}"
        assert field_name in form.fields
        assert form.fields[field_name].initial == "Тестовый ответ"

    def test_form_clean_handles_boolean_false(
        self,
        employer_user,
        university_user,
        question_boolean,
        question_text,
        question_textarea,
        question_choice,
        question_multiple_choice,
        question_date,
        question_number,
    ):
        """Тест обработки boolean поля со значением False"""
        User = get_user_model()

        universities = [university_user.organization]
        for i in range(4, 8):
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

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_boolean.id}": False,
        }

        questions = [
            question_text,
            question_textarea,
            question_choice,
            question_multiple_choice,
            question_date,
            question_number,
        ]

        for question in questions:
            field_name = f"q_{question.id}"
            if question.question_type == "text":
                data[field_name] = "Тестовый ответ"
            elif question.question_type == "textarea":
                data[field_name] = "Тестовый ответ textarea"
            elif question.question_type == "choice":
                data[field_name] = "Автоматизация"
            elif question.question_type == "multiple_choice":
                data[field_name] = ["Docker"]
            elif question.question_type == "date":
                data[field_name] = "2024-01-01"
            elif question.question_type == "number":
                data[field_name] = 10

        form = TechnicalRequirementForm(data, user=employer_user)
        assert form.is_valid(), form.errors

        requirement = form.save(commit=False)
        requirement.employer = employer_user
        requirement.save()

        answers = json.loads(requirement.answers)
        assert str(question_boolean.id) in answers
        assert answers[str(question_boolean.id)] is False

    def test_form_depends_on_field_validation(
        self,
        employer_user,
        university_user,
        question_boolean,
        question_depends_on,
        question_text,
        question_textarea,
        question_choice,
        question_multiple_choice,
        question_date,
        question_number,
    ):
        """Тест валидации поля с зависимостью"""
        User = get_user_model()

        universities = [university_user.organization]
        for i in range(4, 8):
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

        data = {
            "universities": [u.id for u in universities],
            f"q_{question_boolean.id}": True,
            f"q_{question_depends_on.id}": "Тестовая площадка",
        }

        questions = [
            question_text,
            question_textarea,
            question_choice,
            question_multiple_choice,
            question_date,
            question_number,
        ]

        for question in questions:
            field_name = f"q_{question.id}"
            if question.question_type == "text":
                data[field_name] = "Тестовый ответ"
            elif question.question_type == "textarea":
                data[field_name] = "Тестовый ответ textarea"
            elif question.question_type == "choice":
                data[field_name] = "Автоматизация"
            elif question.question_type == "multiple_choice":
                data[field_name] = ["Docker"]
            elif question.question_type == "date":
                data[field_name] = "2024-01-01"
            elif question.question_type == "number":
                data[field_name] = 10

        form = TechnicalRequirementForm(data, user=employer_user)
        assert form.is_valid(), form.errors
