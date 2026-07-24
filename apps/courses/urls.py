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
    # Детальный просмотр курса
    path(
        "course/<int:course_id>/",
        views.CourseDetailView.as_view(),
        name="course_detail",
    ),
    # Для ВУЗа - список курсов с выбранными работниками
    path(
        "university/selected-courses/",
        views.UniversitySelectedCoursesListView.as_view(),
        name="university_selected_courses",
    ),
    path(
        "university/selected-courses/<int:course_id>/employees/",
        views.UniversitySelectedCourseEmployeesView.as_view(),
        name="university_selected_course_employees",
    ),
]
