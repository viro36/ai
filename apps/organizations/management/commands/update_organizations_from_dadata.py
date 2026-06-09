import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.organizations.models import Organization
from apps.organizations.dadata_client import get_organization_by_inn

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Обновляет данные организаций из DaData"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Обновить все организации",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Максимальное количество организаций для обновления (по умолчанию None - без ограничений)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Задержка между запросами в секундах (по умолчанию 0.5)",
        )
        parser.add_argument(
            "--inn",
            type=str,
            help="Обновить организацию по конкретному ИНН",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Обновлять организации, не обновлявшиеся N дней (по умолчанию 7)",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f"=== Начало обновления организаций из DaData ===")
        )
        self.stdout.write(f'Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

        # Определяем, какие организации обновлять
        if options["inn"]:
            queryset = Organization.objects.filter(inn=options["inn"])
            self.stdout.write(f'Обновляем организацию с ИНН: {options["inn"]}')
        elif options["all"]:
            queryset = Organization.objects.all()
            if options["limit"]:
                queryset = queryset[: options["limit"]]
                self.stdout.write(
                    f'Обновляем организации (ограничение: {options["limit"]})'
                )
            else:
                self.stdout.write(f"Обновляем ВСЕ организации (без ограничений)")
        else:
            # По умолчанию обновляем только те, которые не обновлялись N дней
            from django.utils import timezone
            from datetime import timedelta

            days_ago = timezone.now() - timedelta(days=options["days"])
            queryset = Organization.objects.filter(updated_at__lt=days_ago).order_by(
                "updated_at"
            )

            if options["limit"]:
                queryset = queryset[: options["limit"]]

            self.stdout.write(
                f'Обновляем организации, не обновлявшиеся {options["days"]} дней'
            )

        total = queryset.count()
        self.stdout.write(f"Найдено организаций для обновления: {total}\n")

        if total == 0:
            self.stdout.write(self.style.WARNING("Нет организаций для обновления"))
            return

        success_count = 0
        error_count = 0
        skip_count = 0

        # Список полей для обновления
        fields_to_update = [
            ("kpp", "kpp"),
            ("kpp_largest", "kpp_largest"),
            ("ogrn", "ogrn"),
            ("ogrn_date", "ogrn_date"),
            ("hid", "hid"),
            ("org_type", "org_type"),
            ("full_name", "full_name"),
            ("short_name", "short_name"),
            ("full_name_without_opf", "full_name_without_opf"),
            ("short_name_without_opf", "short_name_without_opf"),
            ("latin_name", "latin_name"),
            ("fio_surname", "fio_surname"),
            ("fio_name", "fio_name"),
            ("fio_patronymic", "fio_patronymic"),
            ("opf_code", "opf_code"),
            ("opf_full", "opf_full"),
            ("opf_short", "opf_short"),
            ("opf_type", "opf_type"),
            ("address_raw", "address_raw"),
            ("address_source", "address_source"),
            ("address_qc", "address_qc"),
            ("postal_code", "postal_code"),
            ("region", "region"),
            ("city", "city"),
            ("street", "street"),
            ("house", "house"),
            ("coordinates", "coordinates"),
            ("status", "status"),
            ("status_code", "status_code"),
            ("actuality_date", "actuality_date"),
            ("registration_date", "registration_date"),
            ("liquidation_date", "liquidation_date"),
            ("okpo", "okpo"),
            ("okato", "okato"),
            ("oktmo", "oktmo"),
            ("okogu", "okogu"),
            ("okfs", "okfs"),
            ("okved", "okved"),
            ("okved_type", "okved_type"),
            ("manager_name", "manager_name"),
            ("manager_post", "manager_post"),
            ("manager_start_date", "manager_start_date"),
            ("branch_count", "branch_count"),
            ("branch_type", "branch_type"),
        ]

        for i, org in enumerate(queryset, 1):
            self.stdout.write(
                f"[{i}/{total}] Обновляем {org.short_name} (ИНН: {org.inn})..."
            )

            try:
                # Получаем данные из DaData
                data = get_organization_by_inn(org.inn)

                if not data:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Не удалось получить данные для ИНН {org.inn}"
                        )
                    )
                    error_count += 1
                    continue

                # Обновляем поля
                updated_fields = []
                changed = False

                for field_name, data_key in fields_to_update:
                    new_value = data.get(data_key)
                    old_value = getattr(org, field_name)

                    if new_value is not None and new_value != old_value:
                        setattr(org, field_name, new_value)
                        updated_fields.append(field_name)
                        changed = True

                if changed:
                    with transaction.atomic():
                        org.save()
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Обновлены поля: {", ".join(updated_fields)}'
                            )
                        )
                else:
                    skip_count += 1
                    self.stdout.write(
                        self.style.WARNING("Данные актуальны, обновлений нет")
                    )

                # Задержка между запросами
                if i < total and options["delay"] > 0:
                    time.sleep(options["delay"])

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка: {str(e)}"))
                error_count += 1
                logger.error(f"Ошибка при обновлении организации {org.inn}: {e}")

        # Выводим итоги
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("=== ИТОГИ ОБНОВЛЕНИЯ ==="))
        self.stdout.write(f"Успешно обновлено: {success_count}")
        self.stdout.write(f"Пропущено (актуальные): {skip_count}")
        self.stdout.write(self.style.ERROR(f"Ошибок: {error_count}"))
        self.stdout.write("=" * 50)
