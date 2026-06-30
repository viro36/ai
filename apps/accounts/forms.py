from django import forms
from django.contrib.auth import get_user_model
from apps.organizations.models import District, Organization, OrganizationType
from .models import EmployeeProfile, EmployerProfile, EmployerRegistrationRequest

User = get_user_model()


class EmployerRegistrationForm(forms.ModelForm):
    """Форма регистрации работодателя"""

    username = forms.CharField(
        max_length=150,
        label="Имя пользователя",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Введите имя пользователя"}
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "example@mail.ru"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )
    password_confirm = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Повторите пароль"}
        ),
    )

    short_name = forms.CharField(
        max_length=255,
        label="Краткое название организации",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": 'Например: ООО "Ромашка"'}
        ),
    )
    full_name = forms.CharField(
        label="Полное название организации",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Полное юридическое наименование",
            }
        ),
    )
    inn = forms.CharField(
        max_length=12,
        label="ИНН",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "10 или 12 цифр"}
        ),
    )

    class Meta:
        model = EmployerRegistrationRequest
        fields = ["username", "email", "short_name", "full_name", "inn"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        if EmployerRegistrationRequest.objects.filter(
            username=username, status="pending"
        ).exists():
            raise forms.ValidationError(
                "Заявка с таким именем пользователя уже отправлена на рассмотрение"
            )
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        if EmployerRegistrationRequest.objects.filter(
            email=email, status="pending"
        ).exists():
            raise forms.ValidationError(
                "Заявка с таким email уже отправлена на рассмотрение"
            )
        return email

    def clean_inn(self):
        inn = self.cleaned_data.get("inn")
        # Проверка формата ИНН
        if not inn.isdigit():
            raise forms.ValidationError("ИНН должен содержать только цифры")
        if len(inn) not in [10, 12]:
            raise forms.ValidationError("ИНН должен содержать 10 или 12 цифр")

        # Проверка существования организации
        if Organization.objects.filter(inn=inn).exists():
            org = Organization.objects.get(inn=inn)
            # Не блокируем, а предупреждаем — организация уже есть, но пользователь может к ней привязаться
            self.cleaned_data["existing_organization"] = org
            return inn

        # Проверка наличия pending заявки с таким ИНН
        if EmployerRegistrationRequest.objects.filter(
            inn=inn, status="pending"
        ).exists():
            raise forms.ValidationError(
                "Заявка с таким ИНН уже отправлена на рассмотрение"
            )

        return inn

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")
        return password_confirm


class EmployerProfileForm(forms.ModelForm):
    """Форма профиля работодателя"""

    # Регистрационный email (из CustomUser)
    registration_email = forms.EmailField(
        label="Email для входа (регистрационный)",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "readonly": "readonly"}
        ),
    )

    class Meta:
        model = EmployerProfile
        exclude = ["user"]
        widgets = {
            "actual_address": forms.Textarea(
                attrs={"rows": 2, "class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 XXX XXX-XX-XX"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://"}
            ),
            "contact_person_full_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "contact_person_position": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 XXX XXX-XX-XX"}
            ),
            "contact_person_email": forms.EmailInput(attrs={"class": "form-control"}),
            "checking_account": forms.TextInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "bik": forms.TextInput(attrs={"class": "form-control"}),
            "correspondent_account": forms.TextInput(attrs={"class": "form-control"}),
            "employee_count": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "annual_revenue": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": 0.01}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля необязательными
        for field in self.fields:
            if field != "registration_email":
                self.fields[field].required = False


# --------------------------------------------------------------------------------------


class EmployeeRegistrationForm(forms.ModelForm):
    """Форма регистрации работника (сразу создаёт пользователя)"""

    # Личные данные
    last_name = forms.CharField(
        max_length=150,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        max_length=150,
        label="Имя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    patronymic = forms.CharField(
        max_length=150,
        required=False,
        label="Отчество",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    snils = forms.CharField(
        max_length=14,
        label="СНИЛС",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "000-000-000 00"}
        ),
    )

    # Учётные данные
    username = forms.CharField(
        max_length=150,
        label="Имя пользователя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password_confirm = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    # Фильтры для организации
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        required=False,
        label="Район",
        widget=forms.Select(attrs={"class": "form-control", "id": "district-select"}),
    )
    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.all(),
        required=False,
        label="Тип организации",
        widget=forms.Select(attrs={"class": "form-control", "id": "org-type-select"}),
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label="Организация",
        widget=forms.Select(
            attrs={"class": "form-control", "id": "organization-select"}
        ),
    )

    # Должность
    position = forms.CharField(
        max_length=255,
        label="Должность",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    position_level = forms.ChoiceField(
        choices=EmployeeProfile.POSITION_LEVEL_CHOICES,
        label="Категория должности",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = EmployeeProfile
        fields = ["position", "position_level"]

    def clean_snils(self):
        snils = self.cleaned_data.get("snils")
        snils_clean = snils.replace("-", "").replace(" ", "")
        if not snils_clean.isdigit() or len(snils_clean) != 11:
            raise forms.ValidationError("СНИЛС должен содержать 11 цифр")
        if EmployeeProfile.objects.filter(snils=snils_clean).exists():
            raise forms.ValidationError(
                "Пользователь с таким СНИЛС уже зарегистрирован"
            )
        return snils_clean

    def clean_username(self):
        username = self.cleaned_data.get("username")
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")
        return password_confirm

    def clean_snils(self):
        snils = self.cleaned_data.get("snils")
        snils_clean = snils.replace("-", "").replace(" ", "")
        if not snils_clean.isdigit() or len(snils_clean) != 11:
            raise forms.ValidationError("СНИЛС должен содержать 11 цифр")

        # Проверяем в CustomUser
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if User.objects.filter(snils=snils_clean).exists():
            raise forms.ValidationError(
                "Пользователь с таким СНИЛС уже зарегистрирован"
            )

        # Проверяем в EmployeeProfile
        if EmployeeProfile.objects.filter(snils=snils_clean).exists():
            raise forms.ValidationError(
                "Пользователь с таким СНИЛС уже зарегистрирован"
            )

        return snils_clean


class EmployeeProfileForm(forms.ModelForm):
    """Форма профиля работника"""

    # Поля из CustomUser (для отображения в форме)
    last_name = forms.CharField(
        max_length=150,
        label="Фамилия",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        max_length=150,
        label="Имя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    patronymic = forms.CharField(
        max_length=150,
        required=False,
        label="Отчество",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    birthday = forms.DateField(
        label="Дата рождения",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        input_formats=["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"],
    )
    snils = forms.CharField(
        max_length=14,
        label="СНИЛС",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "000-000-000 00"}
        ),
    )
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    position = forms.CharField(
        max_length=255,
        label="Должность",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            # Анкетные поля (хранятся в EmployeeProfile)
            "gender",  # Пол
            "citizenship",  # Гражданство
            "phone",  # Телефон
            "municipality",  # Муниципалитет
            "locality",  # Населенный пункт
            "position_level",  # Категория должности
            "employment_status",  # Статус занятости
            "work_experience_years",  # Стаж работы
            "education_level",  # Уровень образования
            "education_institution",  # Учебное заведение
            "graduation_year",  # Год окончания
            "specialty",  # Специальность
            "organization",  # Организация (скрытое поле)
            "desired_organization_type",
            "desired_organization",
            "desired_position",
        ]
        widgets = {
            "gender": forms.Select(attrs={"class": "form-control"}),
            "citizenship": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 XXX XXX-XX-XX"}
            ),
            "municipality": forms.TextInput(attrs={"class": "form-control"}),
            "locality": forms.TextInput(attrs={"class": "form-control"}),
            "employment_status": forms.Select(attrs={"class": "form-control"}),
            "work_experience_years": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 70}
            ),
            "education_level": forms.Select(attrs={"class": "form-control"}),
            "education_institution": forms.TextInput(attrs={"class": "form-control"}),
            "graduation_year": forms.NumberInput(
                attrs={"class": "form-control", "min": 1950, "max": 2030}
            ),
            "specialty": forms.TextInput(attrs={"class": "form-control"}),
            "position_level": forms.Select(attrs={"class": "form-control"}),
            "organization": forms.Select(
                attrs={"class": "form-control", "id": "organization-select"}
            ),
            "desired_organization_type": forms.Select(attrs={"class": "form-control"}),
            "desired_organization": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: ООО Ромашка или любая организация в сфере IT",
                }
            ),
            "desired_position": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например: Руководитель отдела, Аналитик данных",
                }
            ),
        }

    # Фильтры для организации (не сохраняются в БД)
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        required=False,
        label="Район",
        widget=forms.Select(attrs={"class": "form-control", "id": "district-select"}),
    )
    organization_type = forms.ModelChoiceField(
        queryset=OrganizationType.objects.all(),
        required=False,
        label="Тип организации",
        widget=forms.Select(attrs={"class": "form-control", "id": "org-type-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization"].required = False
        self.fields["district"].required = False
        self.fields["organization_type"].required = False
        self.fields["desired_organization_type"].required = False
        self.fields["desired_organization"].required = False
        self.fields["desired_position"].required = False
