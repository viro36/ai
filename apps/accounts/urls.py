from django.urls import path
from .views import views, employee_views

app_name = "accounts"

urlpatterns = [
    # Регистрация работодателей
    path("employer/register/", views.employer_register, name="employer_register"),
    path(
        "employer/requests/",
        views.employer_requests_list,
        name="employer_requests_list",
    ),
    path(
        "employer/approve/<int:request_id>/",
        views.approve_employer_request,
        name="approve_employer_request",
    ),
    path(
        "employer/reject/<int:request_id>/",
        views.reject_employer_request,
        name="reject_employer_request",
    ),
    # Регистрация работников
    path("employee/register/", views.employee_register, name="employee_register"),
    # AJAX для фильтрации организаций
    path(
        "get-organizations-ajax/",
        views.get_organizations_ajax,
        name="get_organizations_ajax",
    ),
    # Анкета работадателя
    path("employer/profile/", views.employer_profile, name="employer_profile"),
    # Анкета работника
    path("employee/profile/", views.employee_profile, name="employee_profile"),
    # Список работников
    path(
        "employee-list/",
        employee_views.EmployeeListView.as_view(),
        name="employee_list",
    ),
]
