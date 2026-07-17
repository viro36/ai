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
    path("select/<int:course_id>/", views.select_course, name="select_course"),
    path("selected/", views.selected_courses, name="selected_courses"),
    path(
        "remove/<int:course_id>/",
        views.remove_selected_course,
        name="remove_selected_course",
    ),
]
