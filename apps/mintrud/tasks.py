import logging
import os

import pandas as pd
from celery import shared_task
from django.conf import settings
from django.db import transaction

from apps.mintrud.models import (
    Year,
    NeedType,
    Occupation,
    EconomicActivity,
    LaborNeed,
)
from apps.mintrud.parsing import (
    SHEET_NAME_PATTERN,
    SHEET_PREFIX_TO_NEED_TYPE,
    clean_occupation_code,
    safe_float,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


@shared_task(bind=True, name="mintrud.process_labor_needs_file")
def process_labor_needs_file(
    self, file_name: str, source_name: str, skip_zeros: bool = False
):
    # Превращаем относительный путь в абсолютный
    if not os.path.isabs(file_name):
        file_name = os.path.join(settings.MEDIA_ROOT, file_name)

    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Файл не найден: {file_name}")

    logger.info("Старт обработки файла %s (%s)", source_name, file_name)
    xls = pd.read_excel(file_name, sheet_name=None, header=None)

    processed_sheets = 0
    skipped_sheets = []

    years_cache = {y.year: y for y in Year.objects.all()}
    need_types_cache = {nt.name: nt for nt in NeedType.objects.all()}
    occupations_cache = {o.code: o for o in Occupation.objects.all()}
    activities_cache = {a.name: a for a in EconomicActivity.objects.all()}

    pending_rows = []
    new_occupations = {}
    new_activities = {}

    for sheet_name, df in xls.items():
        sheet_name_clean = str(sheet_name).strip()
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

        if df.shape[0] < 6:
            skipped_sheets.append(sheet_name_clean)
            continue

        activity_headers = df.iloc[4, 3:].tolist()

        row_activities = []
        for name in activity_headers:
            if pd.notna(name) and str(name).strip():
                activity_name = str(name).strip()
                activity = activities_cache.get(activity_name)
                if activity is None:
                    activity = EconomicActivity(name=activity_name)
                    activities_cache[activity_name] = activity
                    new_activities[activity_name] = None
                row_activities.append(activity)
            else:
                row_activities.append(None)

        for _, row in df.iloc[5:].iterrows():
            occupation_code = clean_occupation_code(row[1])
            occupation_name = str(row[2]).strip() if pd.notna(row[2]) else ""

            if not occupation_code or occupation_code == "nan":
                continue
            if not occupation_name or occupation_name == "nan":
                continue

            occupation = occupations_cache.get(occupation_code)
            if occupation is None:
                occupation = Occupation(code=occupation_code, name=occupation_name)
                occupations_cache[occupation_code] = occupation
                new_occupations[occupation_code] = occupation_name

            values = row[3:].tolist()
            for i, value in enumerate(values):
                if i >= len(row_activities):
                    break
                activity = row_activities[i]
                if activity is None:
                    continue
                float_value = safe_float(value)
                if float_value is None:
                    continue
                if skip_zeros and float_value == 0:
                    continue

                pending_rows.append(
                    (
                        year_value,
                        need_type_name,
                        occupation_code,
                        activity.name,
                        float_value,
                    )
                )

        processed_sheets += 1

    total_rows = 0
    with transaction.atomic():
        for year_value in {r[0] for r in pending_rows}:
            if year_value not in years_cache:
                years_cache[year_value] = Year.objects.create(year=year_value)

        for nt_name in {r[1] for r in pending_rows}:
            if nt_name not in need_types_cache:
                need_types_cache[nt_name] = NeedType.objects.create(name=nt_name)

        if new_occupations:
            Occupation.objects.bulk_create(
                list(occupations_cache[c] for c in new_occupations),
                ignore_conflicts=True,
            )
            occupations_cache = {
                o.code: o
                for o in Occupation.objects.filter(
                    code__in=list(occupations_cache.keys())
                )
            }

        if new_activities:
            EconomicActivity.objects.bulk_create(
                list(activities_cache[n] for n in new_activities),
                ignore_conflicts=True,
            )
            activities_cache = {
                a.name: a
                for a in EconomicActivity.objects.filter(
                    name__in=list(activities_cache.keys())
                )
            }

        labor_needs = []
        for year_value, nt_name, occ_code, act_name, value in pending_rows:
            labor_needs.append(
                LaborNeed(
                    year=years_cache[year_value],
                    need_type=need_types_cache[nt_name],
                    occupation=occupations_cache[occ_code],
                    economic_activity=activities_cache[act_name],
                    value=value,
                    source_file=source_name,
                )
            )

        for start in range(0, len(labor_needs), BATCH_SIZE):
            batch = labor_needs[start : start + BATCH_SIZE]
            LaborNeed.objects.bulk_create(
                batch,
                update_conflicts=True,
                unique_fields=[
                    "year",
                    "need_type",
                    "occupation",
                    "economic_activity",
                ],
                update_fields=["value", "source_file", "updated_at"],
                batch_size=BATCH_SIZE,
            )
        total_rows = len(labor_needs)

    logger.info(
        "Готово. Листов: %d, записей: %d, пропущено: %s",
        processed_sheets,
        total_rows,
        skipped_sheets,
    )
    return {
        "processed_sheets": processed_sheets,
        "total_rows": total_rows,
        "skipped_sheets": skipped_sheets,
    }
