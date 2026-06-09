from django.core.management.base import BaseCommand
from apps.organizations.models import District
import json
import os

class Command(BaseCommand):
    help = "Загружает данные из apps/organizations/fixtures/districts.json в базу данных"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='apps/organizations/fixtures/districts.json',
            help='Путь к JSON файлу с данными районов'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден')
            )
            return
        
        # Загружаем данные
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stdout.write(f'Найдено записей в файле: {len(data)}')
            
            created_count = 0
            updated_count = 0
            
            for item in data:
                # Проверяем обязательные поля
                if not all(k in item for k in ['id', 'full_name', 'short_name']):
                    self.stdout.write(
                        self.style.WARNING(f'Пропущена запись с некорректными полями: {item}')
                    )
                    continue
                
                # Создаем или обновляем запись
                district, created = District.objects.update_or_create(
                    pk=item['id'],
                    defaults={
                        'full_name': item['full_name'],
                        'short_name': item['short_name']
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Выводим статистику
            self.stdout.write(
                self.style.SUCCESS(
                    f'Загрузка завершена. Создано: {created_count}, Обновлено: {updated_count}'
                )
            )
            
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка в формате JSON: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Неожиданная ошибка: {e}')
            )
