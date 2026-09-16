import threading
from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ExportJob
from .services import collect_rows, write_xlsx


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "export_type",
        "status_colored",
        "created_by",
        "download_link",
    )
    list_filter = ("export_type", "status", "created_at")
    search_fields = ("created_by__username", "created_by__email")
    readonly_fields = (
        "id",
        "status",
        "file",
        "error_message",
        "filters",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)

    change_list_template = "admin/exports/exportjob/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "start-export/",
                self.admin_site.admin_view(self.start_export_view),
                name="exports_exportjob_start",
            ),
            path(
                "<uuid:job_id>/download/",
                self.admin_site.admin_view(self.download_view),
                name="exports_exportjob_download",
            ),
        ]
        return custom + urls

    # ---------- Кнопки в списке ----------
    @admin.display(description="Статус")
    def status_colored(self, obj):
        colors = {
            "pending": "#f59e0b",
            "done": "#10b981",
            "failed": "#ef4444",
        }
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colors.get(obj.status, "#000"),
            obj.get_status_display(),
        )

    @admin.display(description="Файл")
    def download_link(self, obj):
        if obj.status == "done" and obj.file:
            url = reverse("admin:exports_exportjob_download", args=[obj.id])
            return format_html('<a href="{}">Скачать</a>', url)
        return "—"

    # ---------- Запуск выгрузки ----------
    def start_export_view(self, request):
        """Стартует выгрузку в фоновом потоке."""
        job = ExportJob.objects.create(
            export_type="employees_full",
            created_by=request.user,
            status="pending",
            filters={},
        )

        thread = threading.Thread(
            target=self._run_export,
            args=(job.id,),
            daemon=True,
        )
        thread.start()

        self.message_user(
            request,
            f"Выгрузка запущена (ID: {job.id}). Обновите страницу через несколько секунд.",
            messages.SUCCESS,
        )
        return redirect("admin:exports_exportjob_changelist")

    def _run_export(self, job_id):
        """Фоновая задача: собрать данные и записать Excel."""
        from django.db import close_old_connections

        close_old_connections()

        try:
            job = ExportJob.objects.get(id=job_id)
            rows = collect_rows(job.filters)
            filename = f"employees_full_{job.created_at:%Y%m%d_%H%M%S}.xlsx"

            exports_dir = Path(settings.MEDIA_ROOT) / "exports"
            exports_dir.mkdir(parents=True, exist_ok=True)
            full_path = exports_dir / filename

            write_xlsx(rows, full_path)

            job.file.name = f"exports/{filename}"
            job.status = "done"
            job.error_message = None
            job.save(update_fields=["file", "status", "error_message", "updated_at"])

        except Exception as exc:
            try:
                job = ExportJob.objects.get(id=job_id)
                job.status = "failed"
                job.error_message = f"{type(exc).__name__}: {exc}"
                job.save(update_fields=["status", "error_message", "updated_at"])
            except ExportJob.DoesNotExist:
                pass

    # ---------- Скачивание ----------
    def download_view(self, request, job_id):
        try:
            job = ExportJob.objects.get(id=job_id, status="done")
        except ExportJob.DoesNotExist:
            raise Http404("Файл не найден")

        if not job.file:
            raise Http404("Файл не прикреплён")

        return FileResponse(
            job.file.open("rb"),
            as_attachment=True,
            filename=Path(job.file.name).name,
        )
