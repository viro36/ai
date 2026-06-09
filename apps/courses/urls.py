from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    # Активные курсы
    path(
        "organization/<int:org_id>/courses/",
        views.OrganizationCoursesListView.as_view(),
        name="organization_courses",
    ),
    # Удалённые курсы
    path(
        "organization/<int:org_id>/courses/deleted/",
        views.DeletedCoursesListView.as_view(),
        name="course_deleted_list",
    ),
    # Создание курса
    path(
        "organization/<int:org_id>/courses/add/",
        views.CourseCreateView.as_view(),
        name="course_add",
    ),
    # Редактирование курса
    path(
        "courses/<int:course_id>/edit/",
        views.CourseUpdateView.as_view(),
        name="course_edit",
    ),
    # Мягкое удаление
    path(
        "courses/<int:course_id>/delete/",
        views.CourseSoftDeleteView.as_view(),
        name="course_delete",
    ),
    # Восстановление
    path(
        "courses/<int:course_id>/restore/",
        views.CourseRestoreView.as_view(),
        name="course_restore",
    ),
]
