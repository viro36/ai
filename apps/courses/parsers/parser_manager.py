import logging
from django.contrib import messages

logger = logging.getLogger(__name__)


class ParserManager:
    """Менеджер для управления задачами парсинга через Celery"""

    @classmethod
    def _get_task(cls, parser_key):
        """Возвращает задачу и её название по ключу"""
        from ..tasks import parse_vsuet_courses, parse_vsu_courses, parse_vstu_courses

        task_map = {
            "vsuet": (parse_vsuet_courses, "ВГУИТ"),
            "vsu": (parse_vsu_courses, "ВГУ"),
            "vstu": (parse_vstu_courses, "ВГТУ"),
        }

        return task_map.get(parser_key, (None, None))

    @classmethod
    def run_parser(cls, parser_key, request=None):
        """
        Запуск задачи парсинга через Celery

        Args:
            parser_key: ключ задачи ('vsuet', 'vsu', 'vstu')
            request: объект запроса Django (для сообщений)

        Returns:
            str: ID задачи или None при ошибке
        """
        task, name = cls._get_task(parser_key)

        if not task:
            error_msg = f"Неизвестная задача: {parser_key}"
            if request:
                messages.error(request, error_msg)
            logger.error(error_msg)
            return None

        try:
            # Запускаем задачу асинхронно
            result = task.delay()
            task_id = result.id

            success_msg = f'Задача "{name}" запущена (ID: {task_id[:8]}...)'
            if request:
                messages.info(request, success_msg)
            logger.info(success_msg)
            return task_id

        except Exception as e:
            error_msg = f'Ошибка при запуске задачи "{name}": {str(e)}'
            if request:
                messages.error(request, error_msg)
            logger.error(error_msg, exc_info=True)
            return None

    @classmethod
    def run_all_parsers(cls, request=None):
        """Запуск всех задач парсинга"""
        results = {}
        success_tasks = []

        for key in ["vsuet", "vsu", "vstu"]:
            task, name = cls._get_task(key)
            if task:
                try:
                    result = task.delay()
                    results[key] = result.id
                    success_tasks.append(name)
                    logger.info(f'Задача "{name}" запущена, ID: {result.id[:8]}...')
                except Exception as e:
                    results[key] = None
                    logger.error(f'Ошибка запуска "{name}": {e}')

        if request and success_tasks:
            messages.success(
                request, f'Задачи запущены!<br>{"<br>".join(success_tasks)}'
            )
        elif request and not success_tasks:
            messages.error(request, "Не удалось запустить ни одной задачи")

        return results
