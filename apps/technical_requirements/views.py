from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView

from apps.organizations.models import Organization
from .models import (
    TechnicalRequirement,
    Question,
    RequirementStatus,
    TechnicalRequirementUniversity,
)
from .forms import TechnicalRequirementForm


@login_required
def create_technical_requirement(request):
    """Создание технического задания"""
    if request.user.user_type not in ["employer", "admin"]:
        messages.error(request, "Доступ запрещён")
        return redirect("home")

    if request.method == "POST":
        form = TechnicalRequirementForm(request.POST, user=request.user)

        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.employer = request.user
            requirement.save()

            # Создаем связь с каждым выбранным ВУЗом со статусом "Отправлено"
            sent_status = RequirementStatus.objects.get(code=1)
            universities = form.cleaned_data.get("universities", [])
            for university in universities:
                TechnicalRequirementUniversity.objects.create(
                    technical_requirement=requirement,
                    university=university,
                    status=sent_status,
                )

            messages.success(
                request,
                f"Техническое задание успешно создано и отправлено {len(universities)} ВУЗам!",
            )
            return redirect("technical_requirements:my_requirements")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = TechnicalRequirementForm(user=request.user)

    questions = Question.objects.filter(is_active=True).order_by("order")

    universities_queryset = (
        Organization.objects.filter(users__user_type="university")
        .distinct()
        .order_by("short_name")
    )

    context = {
        "form": form,
        "questions": questions,
        "is_create": True,
        "universities_count": universities_queryset.count(),
    }
    return render(request, "technical_requirements/requirement_form.html", context)


class MyRequirementsListView(LoginRequiredMixin, ListView):
    """Список технических заданий работодателя"""

    model = TechnicalRequirement
    template_name = "technical_requirements/my_requirements.html"
    context_object_name = "requirements"
    paginate_by = 20

    def get_queryset(self):
        return (
            TechnicalRequirement.objects.filter(employer=self.request.user)
            .prefetch_related(
                "university_statuses__university", "university_statuses__status"
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все статусы для отображения
        context["statuses"] = RequirementStatus.objects.filter(is_active=True).order_by(
            "order"
        )
        return context


class ReceivedRequirementsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список полученных технических заданий для ВУЗа"""

    model = TechnicalRequirementUniversity
    template_name = "technical_requirements/received_requirements.html"
    context_object_name = "requirements"
    paginate_by = 20

    def test_func(self):
        return self.request.user.user_type in ["university", "admin"]

    def get_queryset(self):
        user = self.request.user
        search_query = self.request.GET.get("search", "").strip()
        status_filter = self.request.GET.get("status", "")

        if user.user_type == "admin":
            queryset = TechnicalRequirementUniversity.objects.all()
        else:
            queryset = TechnicalRequirementUniversity.objects.filter(
                university=user.organization
            )

        # Поиск по организации работодателя
        if search_query:
            queryset = queryset.filter(
                technical_requirement__employer__organization__short_name__icontains=search_query
            )

        # Фильтр по статусу
        if status_filter:
            queryset = queryset.filter(status_id=status_filter)

        return queryset.select_related(
            "technical_requirement",
            "technical_requirement__employer",
            "technical_requirement__employer__organization",
            "status",
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = RequirementStatus.objects.filter(is_active=True).order_by(
            "order"
        )
        context["search_query"] = self.request.GET.get("search", "")
        context["selected_status"] = self.request.GET.get("status", "")
        return context


class RequirementDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр технического задания"""

    model = TechnicalRequirement
    template_name = "technical_requirements/requirement_detail.html"
    context_object_name = "requirement"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "employer":
            return TechnicalRequirement.objects.filter(employer=user)
        elif user.user_type == "university":
            return TechnicalRequirement.objects.filter(
                university_statuses__university=user.organization
            )
        return TechnicalRequirement.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = Question.objects.filter(is_active=True).order_by("order")

        # Получаем статусы для всех ВУЗов этого ТЗ
        requirement = context["requirement"]
        context["university_statuses"] = TechnicalRequirementUniversity.objects.filter(
            technical_requirement=requirement
        ).select_related("university", "status")

        return context


@login_required
def delete_technical_requirement(request, pk):
    """Удаление технического задания"""
    requirement = get_object_or_404(TechnicalRequirement, pk=pk, employer=request.user)

    if request.method == "POST":
        requirement.delete()
        messages.success(request, "Техническое задание удалено")
        return redirect("technical_requirements:my_requirements")

    return redirect("technical_requirements:my_requirements")


@login_required
def update_requirement_status(request, pk):
    """Обновление статуса технического задания для ВУЗа"""
    requirement_university = get_object_or_404(TechnicalRequirementUniversity, pk=pk)

    # Проверяем, что ВУЗ имеет доступ к этому заданию
    if request.user.user_type == "university":
        if requirement_university.university != request.user.organization:
            messages.error(request, "У вас нет доступа к этому заданию")
            return redirect("technical_requirements:received_requirements")
    else:
        messages.error(request, "Только ВУЗы могут изменять статус")
        return redirect("technical_requirements:received_requirements")

    if request.method == "POST":
        status_id = request.POST.get("status_id")
        if status_id:
            try:
                status = RequirementStatus.objects.get(id=status_id)
                requirement_university.status = status
                requirement_university.save()
                messages.success(
                    request,
                    f'Статус задания #{requirement_university.technical_requirement.id} изменён на "{status.name}"',
                )
            except RequirementStatus.DoesNotExist:
                messages.error(request, "Выбранный статус не существует")
        else:
            messages.error(request, "Статус не выбран")

    return redirect("technical_requirements:received_requirements")


@login_required
def requirement_statuses(request, pk):
    """Список статусов ТЗ по ВУЗам"""
    requirement = get_object_or_404(TechnicalRequirement, pk=pk, employer=request.user)

    university_statuses = TechnicalRequirementUniversity.objects.filter(
        technical_requirement=requirement
    ).select_related("university", "status")

    context = {
        "requirement": requirement,
        "university_statuses": university_statuses,
    }
    return render(request, "technical_requirements/requirement_statuses.html", context)
