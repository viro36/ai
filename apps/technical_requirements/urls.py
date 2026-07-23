from django.urls import path
from . import views

app_name = "technical_requirements"

urlpatterns = [
    # Для работодателя
    path("create/", views.create_technical_requirement, name="create"),
    path("my/", views.MyRequirementsListView.as_view(), name="my_requirements"),
    path("delete/<int:pk>/", views.delete_technical_requirement, name="delete"),
    # Для ВУЗа
    path(
        "received/",
        views.ReceivedRequirementsListView.as_view(),
        name="received_requirements",
    ),
    path("detail/<int:pk>/", views.RequirementDetailView.as_view(), name="detail"),
    path(
        "update-status/<int:pk>/", views.update_requirement_status, name="update_status"
    ),
    path("statuses/<int:pk>/", views.requirement_statuses, name="requirement_statuses"),
]
