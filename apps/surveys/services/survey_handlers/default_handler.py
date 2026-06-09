from .base import BaseSurveyHandler


class DefaultSurveyHandler(BaseSurveyHandler):
    """Обработчик для стандартных опросов (без специальной логики)"""

    @classmethod
    def can_handle(cls, category):
        """По умолчанию обрабатывает все опросы, которые не обработаны другими"""
        return True

    def calculate_results(self, user_responses):
        """Для стандартных опросов просто возвращаем None"""
        return None

    def get_results_context(self, results):
        """Стандартный контекст"""
        return {
            "is_default": True,
        }

    def get_results_template(self):
        return "surveys/components/default_results.html"
