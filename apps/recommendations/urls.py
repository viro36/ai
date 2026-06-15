from django.urls import path
from . import views

app_name = "recommendations"

urlpatterns = [
    path("", views.my_recommendations, name="my_recommendations"),
    path("generate/", views.generate_recommendations, name="generate_recommendations"),
    path(
        "regenerate/",
        views.regenerate_recommendations,
        name="regenerate_recommendations",
    ),
    path("status/", views.check_recommendations_status, name="check_status"),
]
