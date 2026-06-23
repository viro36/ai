import logging

from .vsuet_parser import VsuetParser
from .vsu_parser import VsuParser
from .vstu_parser import VstuParser
from .vgltu_parser import VgltuParser
from .vspu_parser import VspuParser
from .vepi_parser import VepiParser
from .vgas_parser import VgasParser
from .vivt_parser import VivtParser

logger = logging.getLogger(__name__)


class ParserManager:
    """Менеджер парсеров курсов"""

    _parsers = {
        "vsuet": VsuetParser,
        "vsu": VsuParser,
        "vstu": VstuParser,
        "vgltu": VgltuParser,
        "vspu": VspuParser,
        "vepi": VepiParser,
        "vgas": VgasParser,
        "vivt": VivtParser,
    }

    @classmethod
    def get_parser(cls, source_name):
        """Получить экземпляр парсера по имени"""
        parser_class = cls._parsers.get(source_name.lower())
        if parser_class:
            return parser_class()
        return None

    @classmethod
    def run_parser(cls, source_name, request=None):
        """Запустить парсинг указанного источника"""
        parser = cls.get_parser(source_name)
        if not parser:
            logger.error(f"Парсер {source_name} не найден")
            return {"status": "error", "message": f"Парсер {source_name} не найден"}

        try:
            result = parser.run()
            if request:
                # Сообщение для админки
                from django.contrib import messages

                messages.success(
                    request,
                    f"Парсинг {parser.organization.short_name} завершён! "
                    f"Добавлено: {result.get('created', 0)}, "
                    f"Обновлено: {result.get('updated', 0)}",
                )
            return result
        except Exception as e:
            logger.error(f"Ошибка при парсинге {source_name}: {e}")
            if request:
                from django.contrib import messages

                messages.error(request, f"Ошибка парсинга {source_name}: {str(e)}")
            return {"status": "error", "message": str(e)}

    @classmethod
    def run_all_parsers(cls, request=None):
        """Запустить все парсеры"""
        results = {}
        for name in cls._parsers:
            results[name] = cls.run_parser(name, request)
        return results
