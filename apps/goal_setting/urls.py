from django.urls import path
from . import views

app_name = "goal_setting"

urlpatterns = [
    path("", views.goal_setting_view, name="goal_setting"),
]
