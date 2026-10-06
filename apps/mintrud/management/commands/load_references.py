from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import pandas as pd

from apps.mintrud.models import Occupation, EconomicActivity
from apps.mintrud.parsing import clean_occupation_code


class Command(BaseCommand):
    help = "Загружает справочники занятий и видов деятельности из Excel файла"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]
        try:
            xl = pd.ExcelFile(file_path)
            if not xl.sheet_names:
                raise CommandError("В файле нет листов.")

            sheet_name = xl.sheet_names[0]
            self.stdout.write(f"Читаем лист: {sheet_name}")

            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

            if df.shape[0] < 6:
                raise CommandError(f"Слишком мало строк в листе '{sheet_name}'.")

            with transaction.atomic():
                # Виды деятельности
                activity_headers = df.iloc[4, 3:].tolist()
                existing_activities = set(
                    EconomicActivity.objects.values_list("name", flat=True)
                )
                to_create = []
                for name in activity_headers:
                    if pd.notna(name) and str(name).strip():
                        clean_name = str(name).strip()
                        if clean_name not in existing_activities:
                            to_create.append(EconomicActivity(name=clean_name))
                            existing_activities.add(clean_name)
                if to_create:
                    EconomicActivity.objects.bulk_create(
                        to_create, ignore_conflicts=True
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Виды деятельности: добавлено {len(to_create)}."
                    )
                )

                # Занятия
                existing_occupations = {o.code: o for o in Occupation.objects.all()}
                to_create_occ = []
                to_update_occ = []

                for _, row in df.iloc[5:].iterrows():
                    code_str = clean_occupation_code(row[1])
                    name_str = str(row[2]).strip() if pd.notna(row[2]) else ""
                    if not code_str or code_str == "nan" or not name_str:
                        continue

                    existing = existing_occupations.get(code_str)
                    if existing is None:
                        to_create_occ.append(Occupation(code=code_str, name=name_str))
                    elif existing.name != name_str:
                        existing.name = name_str
                        to_update_occ.append(existing)

                if to_create_occ:
                    Occupation.objects.bulk_create(to_create_occ, ignore_conflicts=True)
                if to_update_occ:
                    Occupation.objects.bulk_update(
                        to_update_occ, ["name"], batch_size=1000
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Занятия: создано {len(to_create_occ)}, обновлено {len(to_update_occ)}."
                    )
                )

        except CommandError:
            raise
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка: {e}"))
            raise
