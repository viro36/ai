from celery import shared_task
from .parsers.parser_manager import ParserManager
import logging

logger = logging.getLogger(__name__)

# Сопоставление названий вузов и их парсеров
UNIVERSITY_PARSERS = {
    "ВГУИТ": "vsuet",
    "ВГУ": "vsu",
    "ВГТУ": "vstu",
    "ВГЛТУ": "vgltu",
    "ВГПУ": "vspu",
    "ВЭПИ": "vepi",
    "ВГАС": "vgas",
    "ВИВТ": "vivt",
}


def run_parser_task(parser_name, university_name):
    """Общая логика запуска парсера"""
    parser = ParserManager.get_parser(parser_name)
    if not parser:
        return {
            "university": university_name,
            "error": f"Парсер {parser_name} не найден",
        }

    result = parser.run()
    return {
        "university": university_name,
        "created": result.get("created", 0),
        "updated": result.get("updated", 0),
        "total": result.get("created", 0) + result.get("updated", 0),
    }


@shared_task
def parse_university_courses(university_name):
    """Универсальная задача для парсинга любого вуза"""
    parser_name = UNIVERSITY_PARSERS.get(university_name)
    if not parser_name:
        return {
            "university": university_name,
            "error": f"Вуз {university_name} не найден",
        }

    return run_parser_task(parser_name, university_name)


@shared_task
def parse_all_courses():
    """Парсинг всех курсов (параллельно)"""
    from celery import group

    # Создаём группу задач для всех вузов
    tasks = [parse_university_courses.s(name) for name in UNIVERSITY_PARSERS.keys()]

    # Запускаем все задачи параллельно
    job = group(tasks)
    result = job.apply_async()

    # Ждём завершения всех задач
    results = result.get(timeout=600)

    return results


@shared_task
def parse_vsuet_courses():
    return parse_university_courses("ВГУИТ")


@shared_task
def parse_vsu_courses():
    return parse_university_courses("ВГУ")


@shared_task
def parse_vstu_courses():
    return parse_university_courses("ВГТУ")


@shared_task
def parse_vgltu_courses():
    return parse_university_courses("ВГЛТУ")


@shared_task
def parse_vspu_courses():
    return parse_university_courses("ВГПУ")


@shared_task
def parse_vepi_courses():
    return parse_university_courses("ВЭПИ")


@shared_task
def parse_vgas_courses():
    return parse_university_courses("ВГАС")


@shared_task
def parse_vivt_courses():
    return parse_university_courses("ВИВТ")
