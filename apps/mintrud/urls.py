from django.urls import path
from . import views

app_name = "mintrud"

urlpatterns = [
    path("upload/", views.upload_labor_needs, name="upload_labor_needs"),
]
