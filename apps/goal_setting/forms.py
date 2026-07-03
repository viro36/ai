from django import forms
from .models import Question, QuestionOption, GoalSettingResponse


class GoalSettingForm(forms.Form):
    """Динамическая форма для целеполагания"""

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.questions = Question.objects.filter(is_active=True).order_by("order")

        # Загружаем существующие ответы пользователя
        self.existing_responses = {}
        for response in GoalSettingResponse.objects.filter(user=user).select_related(
            "question", "answer_option"
        ):
            self.existing_responses[response.question_id] = response

        for idx, question in enumerate(self.questions, start=1):
            field_name = f"question_{idx}"
            existing_response = self.existing_responses.get(question.id)

            if question.question_type in ["choice", "multiple_choice"]:
                options = question.options.filter(is_custom=False).order_by("order")
                choices = [(opt.value, opt.label) for opt in options]

                if question.has_custom_option:
                    choices.append(
                        ("custom", question.custom_option_label or "Свой вариант")
                    )

                if question.is_multiple:
                    self.fields[field_name] = forms.MultipleChoiceField(
                        choices=choices,
                        required=question.is_required,
                        label=question.text,
                        help_text=question.description,
                        widget=forms.CheckboxSelectMultiple(
                            attrs={"class": "form-check-input"}
                        ),
                    )
                    if existing_response and existing_response.answer_text:
                        self.fields[field_name].initial = (
                            existing_response.answer_text.split(",")
                        )
                else:
                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=question.is_required,
                        label=question.text,
                        help_text=question.description,
                        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
                    )
                    if existing_response and existing_response.answer_option:
                        initial_value = existing_response.answer_option.value
                        if existing_response.answer_option.is_custom:
                            initial_value = "custom"
                        self.fields[field_name].initial = initial_value

                if question.has_custom_option:
                    custom_field_name = f"{field_name}_custom"
                    self.fields[custom_field_name] = forms.CharField(
                        required=False,
                        label="",
                        widget=forms.TextInput(
                            attrs={
                                "class": "form-control mt-2",
                                "placeholder": "Введите свой вариант...",
                            }
                        ),
                    )
                    if (
                        existing_response
                        and existing_response.answer_text
                        and existing_response.answer_option
                        and existing_response.answer_option.is_custom
                    ):
                        self.fields[custom_field_name].initial = (
                            existing_response.answer_text
                        )

            elif question.question_type == "text":
                self.fields[field_name] = forms.CharField(
                    required=question.is_required,
                    label=question.text,
                    help_text=question.description,
                    widget=forms.Textarea(
                        attrs={
                            "class": "form-control",
                            "rows": 4,
                            "placeholder": question.description
                            or "Введите ваш ответ...",
                        }
                    ),
                    max_length=question.max_length or 500,
                )
                if existing_response:
                    self.fields[field_name].initial = existing_response.answer_text

            elif question.question_type == "date_range":
                start_field_name = f"{field_name}_start"
                self.fields[start_field_name] = forms.DateField(
                    required=question.is_required,
                    label=f"{question.text} (дата начала)",
                    help_text=question.description,
                    widget=forms.DateInput(
                        attrs={"type": "date", "class": "form-control"}
                    ),
                )
                if existing_response and existing_response.answer_date_start:
                    self.fields[start_field_name].initial = (
                        existing_response.answer_date_start
                    )

                end_field_name = f"{field_name}_end"
                self.fields[end_field_name] = forms.DateField(
                    required=question.is_required,
                    label=f"{question.text} (дата окончания)",
                    widget=forms.DateInput(
                        attrs={"type": "date", "class": "form-control"}
                    ),
                )
                if existing_response and existing_response.answer_date_end:
                    self.fields[end_field_name].initial = (
                        existing_response.answer_date_end
                    )

    def save(self):
        """Сохраняет ответы на вопросы"""
        for idx, question in enumerate(self.questions, start=1):
            field_name = f"question_{idx}"
            response_data = {}

            if question.question_type == "choice":
                selected_value = self.cleaned_data.get(field_name)
                if selected_value:
                    option = QuestionOption.objects.filter(
                        question=question, value=selected_value
                    ).first()

                    if selected_value == "custom":
                        custom_field_name = f"{field_name}_custom"
                        custom_text = self.cleaned_data.get(custom_field_name)
                        if custom_text:
                            # Создаём или получаем опцию "Свой вариант"
                            custom_option, _ = QuestionOption.objects.get_or_create(
                                question=question,
                                value=f"custom_{question.id}",
                                defaults={
                                    "label": custom_text,
                                    "is_custom": True,
                                },
                            )
                            response_data["answer_option"] = custom_option
                            response_data["answer_text"] = custom_text
                    else:
                        if option:
                            response_data["answer_option"] = option
                            # Очищаем текстовое поле, если выбран обычный вариант
                            response_data["answer_text"] = None

            elif question.question_type == "multiple_choice":
                selected_values = self.cleaned_data.get(field_name, [])
                if selected_values:
                    response_data["answer_text"] = ",".join(selected_values)
                    # Очищаем answer_option, так как используется текстовое поле
                    response_data["answer_option"] = None

            elif question.question_type == "text":
                response_data["answer_text"] = self.cleaned_data.get(field_name)

            elif question.question_type == "date_range":
                start_field_name = f"{field_name}_start"
                end_field_name = f"{field_name}_end"
                response_data["answer_date_start"] = self.cleaned_data.get(
                    start_field_name
                )
                response_data["answer_date_end"] = self.cleaned_data.get(end_field_name)

            if response_data:
                GoalSettingResponse.objects.update_or_create(
                    user=self.user, question=question, defaults=response_data
                )
            else:
                # Если ответ пустой — удаляем запись
                GoalSettingResponse.objects.filter(
                    user=self.user, question=question
                ).delete()

        return True
