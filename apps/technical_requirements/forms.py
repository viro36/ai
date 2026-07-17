from django import forms
from .models import TechnicalRequirement, Question
from apps.organizations.models import Organization


class TechnicalRequirementForm(forms.ModelForm):
    """Форма создания технического задания на основе вопросов из БД"""

    class Meta:
        model = TechnicalRequirement
        fields = ["universities", "answers", "status"]
        widgets = {
            "universities": forms.CheckboxSelectMultiple(),
            "answers": forms.HiddenInput(),
            "status": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Делаем поля необязательными в форме
        self.fields["answers"].required = False
        self.fields["status"].required = False

        # Фильтруем только ВУЗы для выбора
        self.fields["universities"].queryset = (
            Organization.objects.filter(users__user_type="university")
            .distinct()
            .order_by("short_name")
        )

        self.fields["universities"].label_from_instance = lambda obj: obj.short_name
        self.fields["universities"].help_text = "Выберите не менее 5 ВУЗов"

        # Получаем все активные вопросы
        self.questions = Question.objects.filter(is_active=True).order_by("order")

        # Создаем поля для каждого вопроса динамически
        for question in self.questions:
            field_name = f"q_{question.id}"

            if question.question_type == "text":
                field = forms.CharField(
                    required=question.is_required,
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": question.placeholder or "",
                            "data-question-id": question.id,
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "textarea":
                field = forms.CharField(
                    required=question.is_required,
                    widget=forms.Textarea(
                        attrs={
                            "class": "form-control",
                            "rows": 4,
                            "placeholder": question.placeholder or "",
                            "data-question-id": question.id,
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "choice":
                choices = [(opt, opt) for opt in (question.options or [])]
                field = forms.ChoiceField(
                    required=question.is_required,
                    choices=choices,
                    widget=forms.Select(
                        attrs={
                            "class": "form-select",
                            "data-question-id": question.id,
                            "data-show-other": (
                                "true"
                                if "Свой вариант" in (question.options or [])
                                else "false"
                            ),
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "multiple_choice":
                choices = [(opt, opt) for opt in (question.options or [])]
                field = forms.MultipleChoiceField(
                    required=question.is_required,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(
                        attrs={
                            "class": "form-check-input",
                            "data-question-id": question.id,
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "boolean":
                field = forms.BooleanField(
                    required=False,
                    widget=forms.CheckboxInput(
                        attrs={
                            "class": "form-check-input",
                            "data-question-id": question.id,
                            "data-boolean": "true",
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "date":
                field = forms.DateField(
                    required=question.is_required,
                    widget=forms.DateInput(
                        attrs={
                            "class": "form-control",
                            "type": "date",
                            "data-question-id": question.id,
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            elif question.question_type == "number":
                field = forms.IntegerField(
                    required=question.is_required,
                    widget=forms.NumberInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": question.placeholder or "",
                            "data-question-id": question.id,
                        }
                    ),
                    label=question.text,
                    help_text=question.help_text or "",
                )
            else:
                continue

            # Добавляем атрибуты для условного отображения
            if question.depends_on:
                field.widget.attrs["data-depends-on"] = f"q_{question.depends_on.id}"
                field.widget.attrs["data-depends-value"] = question.depends_value or ""
                existing_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_class} conditional-field"

            # Сохраняем вопрос в атрибуте поля
            field.question_obj = question

            # Устанавливаем начальное значение из answers
            if self.instance and self.instance.pk:
                initial_value = self.instance.answers.get(str(question.id), "")
                if initial_value:
                    if question.question_type == "multiple_choice":
                        field.initial = (
                            initial_value if isinstance(initial_value, list) else []
                        )
                    else:
                        field.initial = initial_value

            self.fields[field_name] = field

        # Добавляем поля для "Свой вариант" если есть такие вопросы
        for question in self.questions:
            if (
                question.question_type == "choice"
                and question.options
                and "Свой вариант" in question.options
            ):
                other_field_name = f"other_{question.id}"
                self.fields[other_field_name] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control form-control-sm",
                            "placeholder": "Введите свой вариант...",
                            "data-question-id": question.id,
                        }
                    ),
                    label="Укажите свой вариант",
                )

    def clean_universities(self):
        universities = self.cleaned_data.get("universities")
        if universities and universities.count() < 5:
            raise forms.ValidationError("Выберите не менее 5 ВУЗов")
        return universities

    def clean(self):
        cleaned_data = super().clean()

        # Собираем ответы в JSON
        answers = {}
        for question in self.questions:
            field_name = f"q_{question.id}"
            value = cleaned_data.get(field_name)

            # Проверяем обязательность с учётом условного отображения
            if question.is_required:
                # Проверяем, видимо ли поле (зависит от другого вопроса)
                if question.depends_on:
                    depends_field_name = f"q_{question.depends_on.id}"
                    depends_value = cleaned_data.get(depends_field_name)
                    depends_expected = question.depends_value

                    # Если поле скрыто (зависимость не выполнена), пропускаем валидацию
                    if depends_value != depends_expected:
                        continue

                if not value:
                    self.add_error(field_name, "Это поле обязательно для заполнения")
                    continue

            # Обработка "Свой вариант"
            if (
                question.question_type == "choice"
                and question.options
                and "Свой вариант" in question.options
            ):
                if value == "Свой вариант":
                    other_field_name = f"other_{question.id}"
                    other_value = cleaned_data.get(other_field_name)
                    if other_value:
                        answers[str(question.id)] = other_value
                    else:
                        self.add_error(
                            other_field_name, "Пожалуйста, укажите свой вариант"
                        )
                        continue
                else:
                    answers[str(question.id)] = value
            # Для boolean полей сохраняем True/False
            elif question.question_type == "boolean":
                answers[str(question.id)] = bool(value)
            # Для multiple_choice сохраняем список
            elif question.question_type == "multiple_choice":
                answers[str(question.id)] = value or []
            # Для date полей преобразуем в строку
            elif question.question_type == "date" and value:
                if hasattr(value, "isoformat"):
                    answers[str(question.id)] = value.isoformat()
                else:
                    answers[str(question.id)] = str(value)
            else:
                answers[str(question.id)] = value

            # Очищаем поле, чтобы не сохранять его в модели
            cleaned_data.pop(field_name, None)

        # Удаляем поля "other_" из cleaned_data
        for key in list(cleaned_data.keys()):
            if key.startswith("other_"):
                cleaned_data.pop(key, None)

        # Преобразуем словарь в JSON строку для JSONField
        import json

        # Используем default параметр для обработки всех типов
        cleaned_data["answers"] = json.dumps(answers, ensure_ascii=False, default=str)

        if not cleaned_data.get("status"):
            cleaned_data["status"] = "draft"

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
