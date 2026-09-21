import pandas as pd
from django.core.management.base import BaseCommand
from apps.mintrud.models import Occupation, EconomicActivity


class Command(BaseCommand):
    help = "Загружает справочники занятий и видов деятельности из Excel файла"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Путь к Excel файлу")

    def handle(self, *args, **options):
        file_path = options["file_path"]
        try:
            # Читаем первый лист, чтобы получить справочники
            df = pd.read_excel(file_path, sheet_name=0, header=None)

            # Загружаем виды экономической деятельности
            activity_headers = df.iloc[3, 2:].tolist()
            for name in activity_headers:
                if pd.notna(name) and name:
                    EconomicActivity.objects.get_or_create(name=name.strip())
            self.stdout.write(
                self.style.SUCCESS("Справочник видов деятельности обновлен.")
            )

            # Загружаем занятия
            for index, row in df.iloc[4:].iterrows():
                occupation_code = str(row[0]).strip()
                occupation_name = str(row[1]).strip()
                if occupation_code and occupation_name and occupation_code != "nan":
                    Occupation.objects.get_or_create(
                        code=occupation_code, defaults={"name": occupation_name}
                    )
            self.stdout.write(self.style.SUCCESS("Справочник занятий обновлен."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка: {e}"))
