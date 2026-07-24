from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.http import HttpResponseForbidden, Http404
from django.db.models import Q, Count, Exists, OuterRef
from apps.users.models import CustomUser
from apps.recommendations.models import SelectedCourse


class EmployeeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список работников организации для работодателя"""

    model = CustomUser
    template_name = "accounts/employee/employee_list.html"
    context_object_name = "employees"
    paginate_by = 20

    def test_func(self):
        return self.request.user.user_type == "employer"

    def handle_no_permission(self):
        return HttpResponseForbidden("Доступ запрещён")

    def get_queryset(self):
        organization = self.request.user.organization
        if not organization:
            return CustomUser.objects.none()

        search_query = self.request.GET.get("search", "")
        queryset = CustomUser.objects.filter(
            organization=organization, user_type="employee", is_active=True
        ).select_related("employee_profile")

        queryset = queryset.annotate(
            recommendations_count=Count("course_recommendations", distinct=True),
            selected_courses_count=Count("selected_courses", distinct=True),
            has_selected_courses=Exists(
                SelectedCourse.objects.filter(user=OuterRef("pk"))
            ),
        )

        if search_query:
            queryset = queryset.filter(
                Q(last_name__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(patronymic__icontains=search_query)
                | Q(employee_profile__position__icontains=search_query)
            )

        return queryset.order_by("last_name", "first_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.request.user.organization
        context["total_count"] = self.get_queryset().count()
        return context


class EmployeeSelectedCoursesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список выбранных курсов сотрудника для работодателя (без кнопки удалить)"""

    model = SelectedCourse
    template_name = "accounts/employee/employee_selected_courses.html"
    context_object_name = "selected_courses"
    paginate_by = 20

    def test_func(self):
        return self.request.user.user_type == "employer"

    def handle_no_permission(self):
        return HttpResponseForbidden("Доступ запрещён")

    def get_queryset(self):
        employee_id = self.kwargs.get("employee_id")
        try:
            employee = CustomUser.objects.get(
                id=employee_id,
                organization=self.request.user.organization,
                user_type="employee",
                is_active=True,
            )
        except CustomUser.DoesNotExist:
            raise Http404("Сотрудник не найден")

        return (
            SelectedCourse.objects.filter(user=employee)
            .select_related("course", "course__organization")
            .prefetch_related("approval")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_id = self.kwargs.get("employee_id")
        employee = CustomUser.objects.get(id=employee_id)
        context["employee"] = employee
        context["total"] = self.get_queryset().count()
        return context
