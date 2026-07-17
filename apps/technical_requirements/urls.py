from django.urls import path
from . import views

app_name = "technical_requirements"

urlpatterns = [
    # Для работодателя
    path("create/", views.create_technical_requirement, name="create"),
    path("my/", views.MyRequirementsListView.as_view(), name="my_requirements"),
    path("edit/<int:pk>/", views.edit_technical_requirement, name="edit"),
    path("delete/<int:pk>/", views.delete_technical_requirement, name="delete"),
    path("send/<int:pk>/", views.send_technical_requirement, name="send"),
    # Для ВУЗа
    path(
        "received/",
        views.ReceivedRequirementsListView.as_view(),
        name="received_requirements",
    ),
    path("detail/<int:pk>/", views.RequirementDetailView.as_view(), name="detail"),
]
