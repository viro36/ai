from django.urls import path
from apps.coverage_analysis import views

app_name = "coverage_analysis"

urlpatterns = [
    path(
        "download/<str:scenario>/",
        views.download_coverage_file,
        name="download_file",
    ),
]
