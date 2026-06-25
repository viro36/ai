from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Course, Category
from .forms import CourseForm
from apps.organizations.models import Organization


class OrganizationAccessMixin(UserPassesTestMixin):
    """Миксин для проверки доступа к курсам организации"""

    def test_func(self):
        user = self.request.user
        if user.user_type not in ["university", "admin"]:
            return False

        # Для CreateView и ListView нужен org_id в kwargs
        if hasattr(self, "get_organization"):
            organization = self.get_organization()
        else:
            # Для UpdateView, DeleteView - берем из курса
            organization = self.get_object().organization

        if user.user_type == "admin":
            return True
        return user.organization == organization

    def handle_no_permission(self):
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Доступ запрещён")

    def get_organization(self):
        """Получение организации из kwargs или из курса"""
        if hasattr(self, "org_id"):
            return get_object_or_404(Organization, id=self.org_id)
        return self.get_object().organization


class OrganizationCoursesListView(
    LoginRequiredMixin, OrganizationAccessMixin, ListView
):
    """Список активных курсов организации"""

    model = Course
    template_name = "courses/organization_courses.html"
    paginate_by = 10
    context_object_name = "courses"

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self._organization = get_object_or_404(
                Organization, id=self.kwargs["org_id"]
            )
        return self._organization

    def get_queryset(self):
        queryset = (
            self.get_organization().courses.filter(is_deleted=False).order_by("-id")
        )

        # Поиск по названию (текстовый ввод)
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        # Фильтр по категории (выпадающий список)
        category_filter = self.request.GET.get("category", "")
        if category_filter:
            queryset = queryset.filter(categories__name=category_filter)
            queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_organization()
        context["search_query"] = self.request.GET.get("search", "")
        context["selected_category"] = self.request.GET.get("category", "")

        categories = (
            Category.objects.filter(
                course__organization=self.get_organization(), course__is_deleted=False
            )
            .values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )

        context["categories"] = list(categories)

        return context


class DeletedCoursesListView(OrganizationCoursesListView):
    """Список удалённых курсов организации"""

    template_name = "courses/course_deleted_list.html"

    def get_queryset(self):
        return (
            self.get_organization()
            .courses.filter(is_deleted=True)
            .order_by("-deleted_at")
        )


class CourseCreateView(LoginRequiredMixin, OrganizationAccessMixin, CreateView):
    """Создание курса"""

    model = Course
    form_class = CourseForm
    template_name = "courses/course_edit.html"

    def get_organization(self):
        if not hasattr(self, "_organization"):
            self._organization = get_object_or_404(
                Organization, id=self.kwargs["org_id"]
            )
        return self._organization

    def form_valid(self, form):
        form.instance.organization = self.get_organization()
        messages.success(self.request, "Курс успешно добавлен!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "courses:organization_courses", kwargs={"org_id": self.kwargs["org_id"]}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_organization()
        context["is_add"] = True
        return context


class CourseUpdateView(LoginRequiredMixin, OrganizationAccessMixin, UpdateView):
    """Редактирование курса"""

    model = Course
    form_class = CourseForm
    template_name = "courses/course_edit.html"
    pk_url_kwarg = "course_id"

    def get_queryset(self):
        return Course.objects.filter(is_deleted=False)

    def form_valid(self, form):
        messages.success(self.request, "Курс успешно обновлён!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "courses:organization_courses",
            kwargs={"org_id": self.object.organization.id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.object.organization
        context["is_add"] = False
        return context


class CourseSoftDeleteView(LoginRequiredMixin, OrganizationAccessMixin, DeleteView):
    """Мягкое удаление курса"""

    model = Course
    template_name = "courses/course_confirm_delete.html"
    pk_url_kwarg = "course_id"

    def get_queryset(self):
        return Course.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_object().organization
        return context

    def post(self, request, *args, **kwargs):
        # Сначала получаем объект (self.object будет установлен)
        self.object = self.get_object()
        course = self.object

        # Выполняем мягкое удаление
        course.is_deleted = True
        course.deleted_at = timezone.now()
        course.save()

        messages.success(request, f'Курс "{course.title}" перемещён в корзину.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Теперь self.object уже существует
        return reverse_lazy(
            "courses:organization_courses",
            kwargs={"org_id": self.object.organization.id},
        )


class CourseRestoreView(LoginRequiredMixin, OrganizationAccessMixin, UpdateView):
    """Восстановление удалённого курса"""

    model = Course
    fields = []
    template_name = "courses/course_confirm_restore.html"
    pk_url_kwarg = "course_id"

    def get_queryset(self):
        return Course.objects.filter(is_deleted=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.get_object().organization
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        course = self.object

        course.is_deleted = False
        course.deleted_at = None
        course.save()

        messages.success(request, f'Курс "{course.title}" восстановлен.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "courses:organization_courses",
            kwargs={"org_id": self.object.organization.id},
        )


class CourseDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница курса"""

    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    pk_url_kwarg = "course_id"

    def get_queryset(self):
        """Показываем только активные курсы"""
        return Course.objects.filter(is_deleted=False)
