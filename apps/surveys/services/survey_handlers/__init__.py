from .default_handler import DefaultSurveyHandler
from .unified_handler import UnifiedSurveyHandler
from .diagnostic_kit_handler import DiagnosticKitHandler


class SurveyHandlerFactory:
    """Фабрика для получения обработчика опроса"""

    _handlers = [
        DiagnosticKitHandler,  # Диагностический комплект руководителя ОО
        UnifiedSurveyHandler,  # DigComp, RIASEC, Big5, Gardner
        DefaultSurveyHandler,  # Всё остальное
    ]

    @classmethod
    def get_handler(cls, category, session):
        for handler_class in cls._handlers:
            if handler_class.can_handle(category):
                return handler_class(category, session)
        return DefaultSurveyHandler(category, session)

    @classmethod
    def register_handler(cls, handler_class):
        cls._handlers.insert(-1, handler_class)
