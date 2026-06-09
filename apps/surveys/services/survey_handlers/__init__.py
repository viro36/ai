from .default_handler import DefaultSurveyHandler
from .unified_handler import UnifiedSurveyHandler


class SurveyHandlerFactory:
    """Фабрика для получения обработчика опроса"""

    _handlers = [
        UnifiedSurveyHandler,  # Универсальный обработчик для DigComp и RIASEC
        DefaultSurveyHandler,  # Для всех остальных опросов
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
