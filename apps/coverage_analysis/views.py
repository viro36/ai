from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404

from apps.coverage_analysis.constants import DOWNLOAD_FILES, DOCS_DIR


@staff_member_required
def download_coverage_file(request, scenario: str):
    """Скачивание исходного Excel-файла анализа покрытия."""
    meta = DOWNLOAD_FILES.get(scenario)
    if not meta:
        raise Http404("Сценарий не найден")

    path = DOCS_DIR / meta["filename"]
    if not path.exists():
        raise Http404("Файл не найден")

    return FileResponse(
        open(path, "rb"),
        as_attachment=True,
        filename=meta["filename"],
        content_type=(
            "application/vnd.openxmlformats-officedocument" ".spreadsheetml.sheet"
        ),
    )
