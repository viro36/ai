import csv
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization, District, OrganizationType


class Command(BaseCommand):
    help = "Импорт организаций из CSV файла (только базовые поля)"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Путь к CSV файлу")
        parser.add_argument(
            "--clear", action="store_true", help="Очистить таблицу перед импортом"
        )

    def get_district(self, district_name):
        """Получает район по названию"""
        if not district_name or district_name.strip() == "":
            return None
        try:
            return District.objects.get(short_name=district_name.strip())
        except District.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'Район "{district_name}" не найден, создаем...')
            )
            return District.objects.create(
                full_name=district_name.strip(), short_name=district_name.strip()
            )

    def get_org_type(self, type_name):
        """Получает или создает тип организации"""
        if not type_name or type_name.strip() == "":
            return None
        type_name = type_name.strip()
        org_type, created = OrganizationType.objects.get_or_create(name=type_name)
        if created:
            self.stdout.write(f'  Создан новый тип: "{type_name}"')
        return org_type

    def parse_coordinates(self, coord_str):
        """Парсит координаты из формата '51.6853497, 39.1751079'"""
        if not coord_str or coord_str.strip() == "":
            return None
        return coord_str.strip()

    def handle(self, *args, **options):
        file_path = options["csv_file"]
        clear_existing = options["clear"]

        if clear_existing:
            self.stdout.write("Очищаем таблицу организаций...")
            Organization.objects.all().delete()

        self.stdout.write(f"Импорт из файла: {file_path}")

        # Для отладки - посмотрим первые символы файла
        with open(file_path, "r", encoding="utf-8-sig") as f:
            first_line = f.readline()
            self.stdout.write(f"Первая строка файла: {first_line[:200]}...")
            f.seek(0)

            # Определяем разделитель
            if "\t" in first_line:
                delimiter = "\t"
                self.stdout.write("Определен разделитель: TAB")
            elif ";" in first_line:
                delimiter = ";"
                self.stdout.write("Определен разделитель: ТОЧКА С ЗАПЯТОЙ")
            else:
                delimiter = ","
                self.stdout.write("Определен разделитель: ЗАПЯТАЯ")

            reader = csv.DictReader(f, delimiter=delimiter)

            # Выводим названия колонок
            self.stdout.write(
                f'Колонки: {list(reader.fieldnames) if reader.fieldnames else "не определены"}'
            )

            count = 0
            errors = 0
            seen_inn = set()

            for row_num, row in enumerate(
                reader, start=2
            ):  # start=2 т.к. 1 строка - заголовок
                try:
                    inn = row.get("ИНН", "").strip()

                    # Пропускаем строки без ИНН
                    if not inn:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Строка {row_num}: пропущена (нет ИНН)"
                            )
                        )
                        continue

                    # Пропускаем дубликаты
                    if inn in seen_inn:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Строка {row_num}: дубликат ИНН={inn}, пропущен"
                            )
                        )
                        continue
                    seen_inn.add(inn)

                    district = self.get_district(row.get("Район", ""))
                    org_type = self.get_org_type(row.get("Тип организации", ""))

                    address = row.get("Адрес одной строкой как в ЕГРЮЛ", "")

                    # Переводим статус
                    status_ru = row.get("Статус организации", "").strip().lower()
                    status_map = {
                        "действующая": "ACTIVE",
                        "ликвидируется": "LIQUIDATING",
                        "ликвидирована": "LIQUIDATED",
                    }
                    status = status_map.get(
                        status_ru, status_ru.upper() if status_ru else "ACTIVE"
                    )

                    org, created = Organization.objects.update_or_create(
                        inn=inn,
                        defaults={
                            "district": district,
                            "organization_type": org_type,
                            "short_name": row.get("Сокращённое название", "")[:500],
                            "full_name": row.get("Полное название", ""),
                            "kpp": row.get("КПП", "").strip() or None,
                            "ogrn": row.get("ОГРН", "").strip() or None,
                            "address_raw": address,
                            "coordinates": self.parse_coordinates(
                                row.get("Координаты")
                            ),
                            "status": status,
                        },
                    )

                    if created:
                        count += 1
                        self.stdout.write(
                            f"  + [{row_num}] Добавлена: {org.short_name or org.inn}"
                        )
                    else:
                        self.stdout.write(
                            f"  ~ [{row_num}] Обновлена: {org.short_name or org.inn}"
                        )

                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f"  Ошибка в строке {row_num}: {str(e)[:100]}")
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nИмпорт завершен. Добавлено: {count}, Ошибок: {errors}, Всего строк: {row_num-1}"
                )
            )
