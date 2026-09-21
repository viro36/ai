from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Выберите Excel файл",
        help_text="Файл должен быть в формате .xlsx. Тип потребности ('Общее' или 'Замещение') "
        "и год определяются автоматически из названий листов (например, 'Общ__2027', 'Замещ__2027').",
    )
