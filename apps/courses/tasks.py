from celery import shared_task
from .parsers.vsuet_parser import VsuetParser
from .parsers.vsu_parser import VsuParser
from .parsers.vstu_parser import VstuParser


@shared_task
def parse_vsuet_courses():
    """Парсинг курсов ВГУИТ"""
    parser = VsuetParser()
    created, updated = parser.run()
    return {
        "university": "ВГУИТ",
        "created": created,
        "updated": updated,
        "total": created + updated,
    }


@shared_task
def parse_vsu_courses():
    """Парсинг курсов ВГУ"""
    parser = VsuParser()
    created, updated = parser.run()
    return {
        "university": "ВГУ",
        "created": created,
        "updated": updated,
        "total": created + updated,
    }


@shared_task
def parse_vstu_courses():
    """Парсинг курсов ВГТУ"""
    parser = VstuParser()
    created, updated = parser.run()
    return {
        "university": "ВГТУ",
        "created": created,
        "updated": updated,
        "total": created + updated,
    }


# задача для запуска всех парсеров последовательно
@shared_task
def parse_all_courses():
    """Парсинг всех курсов (последовательно)"""
    results = []

    tasks = [
        (parse_vsuet_courses, "ВГУИТ"),
        (parse_vsu_courses, "ВГУ"),
        (parse_vstu_courses, "ВГТУ"),
    ]

    for task, name in tasks:
        try:
            result = task.apply().get(timeout=300)  # 5 минут на каждый
            results.append(result)
        except Exception as e:
            results.append({"university": name, "error": str(e)})

    return results
