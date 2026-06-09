from abc import ABC, abstractmethod
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseSurveyHandler(ABC):
    """Базовый класс для обработчиков опросов"""

    def __init__(self, category, session):
        self.category = category
        self.session = session
        self.user = session.user

    @classmethod
    @abstractmethod
    def can_handle(cls, category):
        """Проверяет, может ли этот обработчик обработать данный опрос"""
        pass

    @abstractmethod
    def calculate_results(self, user_responses):
        """Рассчитывает результаты опроса"""
        pass

    @abstractmethod
    def get_results_context(self, results):
        """Возвращает контекст для отображения результатов"""
        pass

    def get_results_template(self):
        """Возвращает шаблон для отображения результатов"""
        return "surveys/components/default_results.html"

    def get_extra_css(self):
        """Возвращает список CSS файлов для результатов"""
        return []

    def get_extra_js(self):
        """Возвращает список JS файлов для результатов"""
        return []
