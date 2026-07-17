from django import template
from django.utils.safestring import mark_safe
from ..models import Question

register = template.Library()


@register.filter
def get_field_value(form, question_id):
    """Получить значение поля по ID вопроса"""
    field_name = f"q_{question_id}"
    try:
        field = form[field_name]
        return field.value()
    except KeyError:
        return None


@register.simple_tag
def render_question_field(form, question):
    """Рендерит поле вопроса с иконкой Font Awesome"""
    field_name = f"q_{question.id}"

    # Получаем поле из формы
    try:
        field = form[field_name]
    except KeyError:
        return mark_safe(
            f'<div class="alert alert-danger">Поле для вопроса #{question.id} не найдено</div>'
        )

    # Определяем иконку в зависимости от типа вопроса
    icon_map = {
        "text": "fa-solid fa-pen",
        "textarea": "fa-solid fa-align-left",
        "choice": "fa-solid fa-angle-down",
        "multiple_choice": "fa-solid fa-list-check",
        "boolean": "fa-solid fa-toggle-on",
        "date": "fa-solid fa-calendar-days",
        "number": "fa-solid fa-hashtag",
    }
    icon = icon_map.get(question.question_type, "fa-solid fa-question")

    # Создаем HTML для поля
    html = f'<div class="form-group" data-question-id="{question.id}"'

    if question.depends_on:
        html += f' data-depends-on="q_{question.depends_on.id}"'
        html += f' data-depends-value="{question.depends_value or ""}"'
        html += ' style="display:none;"'

    html += ">"

    # Заголовок с номером и иконкой
    html += f"""
        <div class="question-label">
            <span class="question-number">
                <i class="{icon}"></i>
            </span>
            <label for="{field.id_for_label}" class="form-label mb-0">
                {question.text}
                {question.is_required and '<span class="required-star">*</span>' or ''}
            </label>
        </div>
    """

    # Помощь
    if question.help_text:
        html += f'<div class="help-text"><i class="fa-solid fa-circle-info me-1"></i>{question.help_text}</div>'

    # Поле
    html += '<div class="mt-2">'

    # Для boolean полей используем переключатель с подписями
    if question.question_type == "boolean":
        # Получаем текущее значение
        current_value = field.value()
        checked = "checked" if current_value else ""

        html += f"""
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox"
                       name="{field_name}"
                       id="{field.id_for_label}"
                       data-question-id="{question.id}"
                       data-boolean="true"
                       {checked}>
                <label class="form-check-label" for="{field.id_for_label}">
                    <span class="badge bg-{"success" if current_value else "secondary"}" id="label_{field.id_for_label}">
                        {"Да" if current_value else "Нет"}
                    </span>
                </label>
            </div>
        """
    else:
        html += field.as_widget()

    html += "</div>"

    # Если это поле выбора и есть вариант "Свой вариант", добавляем поле для ввода
    if (
        question.question_type == "choice"
        and question.options
        and "Свой вариант" in question.options
    ):
        html += f"""
            <div class="other-input-group mt-2" style="display:none;" data-for-question="{question.id}">
                <label for="other_{question.id}" class="form-label small text-muted">
                    <i class="fa-solid fa-pen me-1"></i>Укажите свой вариант:
                </label>
                <input type="text"
                       id="other_{question.id}"
                       name="other_{question.id}"
                       class="form-control form-control-sm"
                       placeholder="Введите свой вариант..."
                       data-question-id="{question.id}">
            </div>
        """

    # Ошибки
    if field.errors:
        html += f'<div class="text-danger mt-1"><i class="fa-solid fa-circle-exclamation me-1"></i>{field.errors}</div>'

    html += "</div>"

    return mark_safe(html)


@register.simple_tag
def render_answer(requirement, question):
    """Рендерит ответ на вопрос для отображения"""
    import json

    if isinstance(requirement, str):
        return mark_safe(
            '<span class="text-muted">Ошибка: неверный формат данных</span>'
        )

    # Получаем answers как словарь
    answers = requirement.answers
    if isinstance(answers, str):
        try:
            answers = json.loads(answers)
        except json.JSONDecodeError:
            answers = {}
    elif not isinstance(answers, dict):
        answers = {}

    answer = answers.get(str(question.id), "")

    if not answer and answer is not False:
        return mark_safe(
            '<span class="text-muted"><i class="fa-regular fa-circle me-1"></i>Не указано</span>'
        )

    # Обработка boolean
    if question.question_type == "boolean":
        # Преобразуем в булево значение
        if isinstance(answer, bool):
            value = answer
        elif isinstance(answer, str):
            value = answer.lower() in ["true", "1", "да"]
        else:
            value = bool(answer)

        if value:
            return mark_safe(
                '<span class="text-success"><i class="fa-regular fa-circle-check me-1"></i>Да</span>'
            )
        return mark_safe(
            '<span class="text-danger"><i class="fa-regular fa-circle-xmark me-1"></i>Нет</span>'
        )

    if question.question_type == "multiple_choice":
        if isinstance(answer, list):
            return mark_safe(", ".join(answer))
        return mark_safe(str(answer))

    if question.question_type == "date":
        try:
            from datetime import date, datetime

            if isinstance(answer, date):
                return mark_safe(answer.strftime("%d.%m.%Y"))
            if isinstance(answer, str):
                try:
                    dt = datetime.fromisoformat(answer)
                    return mark_safe(dt.strftime("%d.%m.%Y"))
                except ValueError:
                    return mark_safe(answer)
        except:
            return mark_safe(str(answer))

    return mark_safe(str(answer))


@register.filter
def get_field(form, field_name):
    """Получить поле формы по имени"""
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter
def get_question(question_id):
    """Получить вопрос по ID"""
    try:
        return Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return None


@register.filter
def get_answer(requirement, question_id):
    """Получить ответ на вопрос из технического задания"""
    return requirement.answers.get(str(question_id), "")
