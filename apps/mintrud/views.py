import uuid

from celery.result import AsyncResult
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from apps.users.models import CustomUser
from .forms import UploadFileForm
from .tasks import process_labor_needs_file


def is_mintrud_user(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.user_type == CustomUser.UserType.MINTUD


@login_required
@user_passes_test(is_mintrud_user)
def upload_labor_needs(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["file"]
            source_name = excel_file.name

            unique_name = f"mintrud_uploads/{uuid.uuid4().hex}_{source_name}"
            saved_path = default_storage.save(unique_name, excel_file)

            skip_zeros = request.POST.get("skip_zeros") == "on"

            task = process_labor_needs_file.delay(
                file_name=saved_path,
                source_name=source_name,
                skip_zeros=skip_zeros,
            )

            messages.success(
                request,
                f"Файл «{source_name}» принят в обработку. " f"ID задачи: {task.id}. ",
            )
            return redirect("mintrud:upload_labor_needs")
    else:
        form = UploadFileForm()

    return render(request, "mintrud/upload.html", {"form": form})


@login_required
@user_passes_test(is_mintrud_user)
def task_status(request, task_id: str):
    """Возвращает статус Celery-задачи в формате JSON."""
    result = AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "state": result.state,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
        "ready": result.ready(),
        "successful": result.successful(),
    }

    if result.ready():
        if result.successful():
            payload["result"] = result.result or {}
        else:
            payload["error"] = str(result.result)
            payload["traceback"] = str(result.traceback)

    return JsonResponse(payload)
