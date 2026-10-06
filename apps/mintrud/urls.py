from django.urls import path
from . import views

app_name = "mintrud"

urlpatterns = [
    path("upload/", views.upload_labor_needs, name="upload_labor_needs"),
    path("task/<str:task_id>/status/", views.task_status, name="task_status"),
]
