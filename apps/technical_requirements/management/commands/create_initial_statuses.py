from django.core.management.base import BaseCommand
from apps.technical_requirements.models import RequirementStatus


class Command(BaseCommand):
    help = "Создает начальные статусы для технических заданий"

    def handle(self, *args, **options):
        statuses_data = [
            {"code": 1, "name": "Отправлено", "color": "#17a2b8", "order": 1},
            {"code": 2, "name": "В разработке", "color": "#ffc107", "order": 2},
            {"code": 3, "name": "Завершено", "color": "#28a745", "order": 3},
            {"code": 4, "name": "Отклонено", "color": "#dc3545", "order": 4},
        ]

        for data in statuses_data:
            status, created = RequirementStatus.objects.get_or_create(
                code=data["code"],
                defaults={
                    "name": data["name"],
                    "color": data["color"],
                    "order": data["order"],
                },
            )
            if created:
                self.stdout.write(f"Создан статус: {status.name}")
            else:
                self.stdout.write(f"Статус уже существует: {status.name}")

        self.stdout.write(self.style.SUCCESS("Начальные статусы успешно созданы!"))
