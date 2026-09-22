from pathlib import Path
from apps.coverage_analysis.models import CoverageScenario

# Папка с исходными Excel-файлами: apps/coverage_analysis/docs/
DOCS_DIR = Path(__file__).resolve().parent / "docs"


# Файлы для скачивания по сценариям
DOWNLOAD_FILES = {
    CoverageScenario.OPTIMISTIC: {
        "filename": "Анализ покрытия потребности кадрами (все по выпускники устраиваются по специальности).xlsx",
        "label": "Оптимистичный сценарий",
    },
    CoverageScenario.REALISTIC: {
        "filename": "Анализ покрытия потребности кадрами(доля выпускников устраивается не по специальности или мигрируют).xlsx",
        "label": "Реалистичный сценарий",
    },
}


def get_download_files():
    """Возвращает список файлов с полными путями и признаком наличия."""
    result = []
    for scenario, meta in DOWNLOAD_FILES.items():
        path = DOCS_DIR / meta["filename"]
        result.append(
            {
                "scenario": scenario,
                "label": meta["label"],
                "filename": meta["filename"],
                "exists": path.exists(),
            }
        )
    return result
