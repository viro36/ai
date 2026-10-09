import re

from apps.surveys.models import (
    DiagnosticKitResult,
    SurveyQuestionOption,
)
from apps.surveys.services.survey_handlers.base import BaseSurveyHandler


class DiagnosticKitHandler(BaseSurveyHandler):
    """Обработчик диагностического комплекта руководителя ОО."""

    def __init__(self, category, session):
        super().__init__(category, session)
        self.survey_config = self.get_survey_config()

    @classmethod
    def can_handle(cls, category):
        name = category.name.lower()
        return "диагностический" in name or "комплект" in name

    def get_survey_config(self):
        return {
            "type": "diagnostic_kit",
            "blocks": 4,
            "max_score_per_block": 10,
            "max_total_score": 40,
            "chart_labels": [
                "Работа 1. Управление образовательной деятельностью и качеством",
                "Работа 2. Администрирование и ресурсное обеспечение",
                "Работа 3. Управление развитием организации",
                "Работа 4. Управление взаимодействием",
            ],
            "result_model": DiagnosticKitResult,
            "score_fields": [
                "work1_score",
                "work2_score",
                "work3_score",
                "work4_score",
            ],
        }

    # ============== Расчёт результатов ==============

    def calculate_results(self, user_responses):
        work_scores = {1: 0, 2: 0, 3: 0, 4: 0}

        for block in self.category.blocks.filter(is_active=True).order_by("order"):
            work_num = self._extract_work_num(block.title)
            if not work_num:
                continue

            for question in block.questions.filter(is_active=True):
                responses = list(
                    user_responses.filter(question=question).exclude(group__isnull=True)
                )
                if not responses:
                    continue

                # Собираем цепочку: {«А»: option_id, «Б»: option_id, ...}
                chain = {r.group: r.selected_option_id for r in responses}

                # Проверяем все группы, которые есть у вопроса
                required_groups = set(
                    question.options.values_list("group", flat=True)
                ) - {None, ""}

                if set(chain.keys()) != required_groups:
                    # Пользователь ответил не на все группы — 0 баллов
                    continue

                all_correct = True
                for letter in required_groups:
                    option_id = chain.get(letter)
                    if not option_id:
                        all_correct = False
                        break
                    try:
                        option = SurveyQuestionOption.objects.get(id=option_id)
                    except SurveyQuestionOption.DoesNotExist:
                        all_correct = False
                        break
                    if not option.is_correct:
                        all_correct = False
                        break

                if all_correct:
                    work_scores[work_num] += 2

        total = sum(work_scores.values())

        result, _ = DiagnosticKitResult.objects.update_or_create(
            session=self.session,
            defaults={
                "work1_score": work_scores[1],
                "work2_score": work_scores[2],
                "work3_score": work_scores[3],
                "work4_score": work_scores[4],
                "total_score": total,
            },
        )
        return result

    def get_results(self):
        try:
            return DiagnosticKitResult.objects.get(session=self.session)
        except DiagnosticKitResult.DoesNotExist:
            return None

    # ============== Контекст для шаблона ==============

    def get_results_context(self, results):
        if results is None:
            return {
                "is_diagnostic_kit": True,
                "works_data": [],
                "total_score": 0,
                "max_total_score": 40,
                "total_level": DiagnosticKitResult.level_for_total(0),
            }

        works_data = results.get_works_data()
        total_level = DiagnosticKitResult.level_for_total(results.total_score)

        return {
            "is_diagnostic_kit": True,
            "survey_result": results,
            "works_data": works_data,
            "total_score": results.total_score,
            "max_total_score": 40,
            "total_level": total_level,
        }

    def get_results_template(self):
        return "surveys/diagnostic_kit_results.html"

    # ============== Вспомогательное ==============

    def _extract_work_num(self, title):
        m = re.search(r"работа\s+(\d)", title, re.IGNORECASE)
        return int(m.group(1)) if m else None
