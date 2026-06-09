import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai.settings")

app = Celery("ai")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Задача для обновления организаций
# @app.task
# def update_organizations_from_dadata():
#     """Задача для периодического обновления организаций из DaData"""
#     from django.core.management import call_command
#     from io import StringIO

#     out = StringIO()
#     # Обновляем все организации без ограничений
#     call_command('update_organizations_from_dadata', '--all', '--delay', '0.5', stdout=out)
#     return out.getvalue()


# # Настройка периодических задач
# app.conf.beat_schedule = {
#     'update-organizations-every-friday': {
#         'task': 'ai.celery.update_organizations_from_dadata',
#         'schedule': crontab(day_of_week='friday', hour=2, minute=0),  # Каждую пятницу в 2:00
#         'args': (),
#     },
# }
