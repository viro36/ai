from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import GoalSettingForm
from .models import GoalSettingResponse


@login_required
def goal_setting_view(request):
    if request.method == "POST":
        form = GoalSettingForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Целеполагание успешно сохранено!")
            return redirect("home")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = GoalSettingForm(request.user)

    # Для прогресса
    questions = form.questions
    total = questions.count()
    answered = GoalSettingResponse.objects.filter(user=request.user).count()
    progress = int(answered / total * 100) if total else 0

    context = {
        "form": form,
        "questions": questions,
        "total_questions": total,
        "progress": progress,
    }
    return render(request, "goal_setting/goal_setting.html", context)
