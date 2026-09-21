import re
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction

from apps.users.models import CustomUser
from .models import Year, NeedType, Occupation, EconomicActivity, LaborNeed
from .forms import UploadFileForm

SHEET_PREFIX_TO_NEED_TYPE = {
    "Общ": "Общее",
    "Замещ": "Замещение",
}

SHEET_NAME_PATTERN = re.compile(r"^(Общ|Замещ)__?(\d{4})$")


def is_mintrud_user(user):
    """Проверка, что пользователь — Минтруд или суперпользователь."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.user_type == CustomUser.UserType.MINTUD


@login_required
@user_passes_test(is_mintrud_user)
def upload_labor_needs(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["file"]

            try:
                # Читаем все листы файла
                xls = pd.read_excel(excel_file, sheet_name=None, header=None)

                # Счётчики для отчёта
                processed_sheets = 0
                skipped_sheets = []
                total_rows = 0

                with transaction.atomic():
                    for sheet_name, df in xls.items():
                        sheet_name_clean = sheet_name.strip()
                        match = SHEET_NAME_PATTERN.match(sheet_name_clean)
                        if not match:
                            skipped_sheets.append(sheet_name_clean)
                            continue

                        prefix, year_str = match.groups()
                        need_type_name = SHEET_PREFIX_TO_NEED_TYPE.get(prefix)
                        if not need_type_name:
                            skipped_sheets.append(sheet_name_clean)
                            continue

                        year_value = int(year_str)
                        year, _ = Year.objects.get_or_create(year=year_value)
                        need_type, _ = NeedType.objects.get_or_create(
                            name=need_type_name
                        )

                        # Заголовки видов деятельности в 4-й строке (индекс 3), начиная с колонки C (индекс 2)
                        activity_headers = df.iloc[3, 2:].tolist()

                        # Создаём/получаем объекты EconomicActivity
                        activities = []
                        for name in activity_headers:
                            if pd.notna(name) and str(name).strip():
                                activity, _ = EconomicActivity.objects.get_or_create(
                                    name=str(name).strip()
                                )
                                activities.append(activity)
                            else:
                                activities.append(None)

                        # Проходим по строкам с данными (с 5-й строки, индекс 4)
                        for index, row in df.iloc[4:].iterrows():
                            occupation_code = str(row[0]).strip()
                            occupation_name = str(row[1]).strip()

                            if (
                                not occupation_code
                                or not occupation_name
                                or occupation_code == "nan"
                            ):
                                continue

                            occupation, created = Occupation.objects.get_or_create(
                                code=occupation_code, defaults={"name": occupation_name}
                            )
                            # На случай, если наименование изменилось — обновим
                            if not created and occupation.name != occupation_name:
                                occupation.name = occupation_name
                                occupation.save(update_fields=["name"])

                            # Значения по видам деятельности
                            values = row[2:].tolist()
                            for i, value in enumerate(values):
                                if i >= len(activities):
                                    break
                                activity = activities[i]
                                if activity is None:
                                    continue
                                if pd.isna(value):
                                    continue
                                try:
                                    float_value = float(value)
                                except (ValueError, TypeError):
                                    continue

                                LaborNeed.objects.update_or_create(
                                    year=year,
                                    need_type=need_type,
                                    occupation=occupation,
                                    economic_activity=activity,
                                    defaults={"value": float_value},
                                )
                                total_rows += 1

                        processed_sheets += 1

                if processed_sheets:
                    messages.success(
                        request,
                        f"Обработано листов: {processed_sheets}. Загружено/обновлено записей: {total_rows}.",
                    )
                else:
                    messages.error(
                        request, "В файле не найдено листов с подходящими названиями."
                    )

                if skipped_sheets:
                    messages.warning(
                        request,
                        "Пропущены листы (не удалось определить тип/год): "
                        + ", ".join(skipped_sheets),
                    )

                return redirect("mintrud:upload_labor_needs")

            except Exception as e:
                messages.error(request, f"Произошла ошибка при обработке файла: {e}")
    else:
        form = UploadFileForm()

    return render(request, "mintrud/upload.html", {"form": form})
