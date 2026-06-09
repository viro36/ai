from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.http import HttpResponseForbidden
from django.db.models import Q
from apps.users.models import CustomUser


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
