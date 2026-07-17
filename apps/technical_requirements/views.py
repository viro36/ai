from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView

from apps.organizations.models import Organization
from .models import TechnicalRequirement, Question
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
            requirement.status = "sent"
            requirement.save()
            form.save_m2m()

            messages.success(
                request,
                f"Техническое задание успешно создано и отправлено {requirement.universities.count()} ВУЗам!",
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


@login_required
def edit_technical_requirement(request, pk):
    """Редактирование технического задания"""
    requirement = get_object_or_404(TechnicalRequirement, pk=pk, employer=request.user)

    if requirement.status != "draft":
        messages.warning(request, "Нельзя редактировать отправленное задание")
        return redirect("technical_requirements:my_requirements")

    if request.method == "POST":
        form = TechnicalRequirementForm(
            request.POST, instance=requirement, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Техническое задание обновлено")
            return redirect("technical_requirements:my_requirements")
    else:
        form = TechnicalRequirementForm(instance=requirement, user=request.user)

    questions = Question.objects.filter(is_active=True).order_by("order")

    universities_queryset = (
        Organization.objects.filter(users__user_type="university")
        .distinct()
        .order_by("short_name")
    )

    context = {
        "form": form,
        "questions": questions,
        "is_create": False,
        "requirement": requirement,
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
            .prefetch_related("universities")
            .order_by("-created_at")
        )


class ReceivedRequirementsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список полученных технических заданий для ВУЗа"""

    model = TechnicalRequirement
    template_name = "technical_requirements/received_requirements.html"
    context_object_name = "requirements"
    paginate_by = 20

    def test_func(self):
        return self.request.user.user_type in ["university", "admin"]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "admin":
            return (
                TechnicalRequirement.objects.filter(status="sent")
                .prefetch_related("universities", "employer")
                .order_by("-created_at")
            )
        return (
            TechnicalRequirement.objects.filter(
                universities=user.organization, status="sent"
            )
            .prefetch_related("employer")
            .order_by("-created_at")
        )


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
            return TechnicalRequirement.objects.filter(universities=user.organization)
        return TechnicalRequirement.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = Question.objects.filter(is_active=True).order_by("order")
        return context


@login_required
def delete_technical_requirement(request, pk):
    """Удаление технического задания (только черновик)"""
    requirement = get_object_or_404(TechnicalRequirement, pk=pk, employer=request.user)

    if requirement.status != "draft":
        messages.warning(request, "Нельзя удалить отправленное задание")
        return redirect("technical_requirements:my_requirements")

    if request.method == "POST":
        requirement.delete()
        messages.success(request, "Техническое задание удалено")
        return redirect("technical_requirements:my_requirements")

    return render(
        request,
        "technical_requirements/requirement_confirm_delete.html",
        {"requirement": requirement},
    )


@login_required
def send_technical_requirement(request, pk):
    """Отправка технического задания ВУЗам"""
    requirement = get_object_or_404(TechnicalRequirement, pk=pk, employer=request.user)

    if requirement.status != "draft":
        messages.warning(request, "Задание уже отправлено")
        return redirect("technical_requirements:my_requirements")

    if requirement.universities.count() < 5:
        messages.warning(request, "Выберите не менее 5 ВУЗов")
        return redirect("technical_requirements:edit", pk=pk)

    if request.method == "POST":
        requirement.status = "sent"
        requirement.save()
        messages.success(
            request,
            f"Техническое задание отправлено {requirement.universities.count()} ВУЗам!",
        )
        return redirect("technical_requirements:my_requirements")

    return render(
        request,
        "technical_requirements/requirement_confirm_send.html",
        {"requirement": requirement},
    )
