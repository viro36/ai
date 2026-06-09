from django import forms
from .models import Course, Category


class CourseForm(forms.ModelForm):
    """Форма для редактирования курса"""

    # Поле для выбора категорий/тегов (множественный выбор)
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control", "size": 5}),
        label="Категории / Теги",
        help_text="Выберите существующие категории (можно несколько). Зажмите Ctrl для выбора нескольких.",
    )

    # Поле для добавления новой категории
    new_category = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Или добавьте новую категорию",
        help_text="Можно добавить несколько категорий через запятую.",
    )

    class Meta:
        model = Course
        fields = [
            "title",
            "url",
            "description",
            "program_type",
            "categories",
            "new_category",
            "field_of_study",
            "duration_hours",
            "duration_weeks",
            "price",
            "study_mode",
            "format",
            "teachers",
            "target_audience",
            "topics",
            "start_dates",
            "document_type",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите название курса"}
            ),
            "url": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://..."}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Описание курса",
                }
            ),
            "program_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Профессиональная переподготовка, Повышение квалификации",
                }
            ),
            "field_of_study": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: 09.03.01 Информатика и вычислительная техника",
                }
            ),
            "duration_hours": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Количество часов"}
            ),
            "duration_weeks": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Например: 2 недели"}
            ),
            "price": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Например: 15000 руб."}
            ),
            "study_mode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Очный, Очно-заочный, Дистанционный",
                }
            ),
            "format": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Лекции, практические занятия, онлайн-трансляции",
                }
            ),
            "teachers": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Преподаватели",
                }
            ),
            "target_audience": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Для кого этот курс",
                }
            ),
            "topics": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Содержание программы",
                }
            ),
            "start_dates": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Сентябрь 2024",
                }
            ),
            "document_type": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Удостоверение о повышении квалификации",
                }
            ),
        }
        labels = {
            "title": "Название курса",
            "url": "Ссылка на курс",
            "description": "Описание",
            "program_type": "Тип программы",
            "categories": "Категории / Теги",
            "field_of_study": "Направление подготовки",
            "duration_hours": "Объём (часы)",
            "duration_weeks": "Продолжительность (недели)",
            "price": "Стоимость",
            "study_mode": "Режим обучения",
            "format": "Форма обучения",
            "teachers": "Преподаватели",
            "target_audience": "Целевая аудитория",
            "topics": "Содержание программы",
            "start_dates": "Даты начала обучения",
            "document_type": "Выдаваемый документ",
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Сохраняем выбранные категории
            if self.cleaned_data.get("categories"):
                instance.categories.set(self.cleaned_data["categories"])
            else:
                instance.categories.clear()

            # Обрабатываем новые категории
            new_category_names = self.cleaned_data.get("new_category", "")
            if new_category_names:
                # Разделяем по запятым, обрезаем пробелы, убираем пустые строки
                names = [
                    name.strip()
                    for name in new_category_names.split(",")
                    if name.strip()
                ]
                # Убираем дубликаты, сохраняя порядок
                unique_names = list(dict.fromkeys(names))
                for name in unique_names:
                    category, _ = Category.objects.get_or_create(name=name)
                    instance.categories.add(category)

        return instance
