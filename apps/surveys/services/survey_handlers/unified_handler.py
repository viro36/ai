from django.db.models import Prefetch

from apps.surveys.models import (
    Big5Result,
    GardnerResult,
    SurveyQuestion,
    SurveyInterpretation,
    DigCompResult,
    RiasacResult,
    RiasecCodeInterpretation,
    ProfessionalStandard,
    GeneralizedLaborFunction,
)
from apps.surveys.services.survey_handlers.base import BaseSurveyHandler


class UnifiedSurveyHandler(BaseSurveyHandler):
    """Универсальный обработчик для опросов"""

    def __init__(self, category, session):
        super().__init__(category, session)
        self.survey_config = self.get_survey_config()

    # ==================================================================
    # КОНФИГУРАЦИЯ
    # ==================================================================

    def get_survey_config(self):
        """Определяет конфигурацию опроса по названию"""
        name = self.category.name.lower()

        # DigCompEdu
        if "digcomp" in name or "цифров" in name:
            return {
                "type": "digcomp",
                "blocks": 5,
                "questions_per_block": 10,
                "max_score_per_block": 50,
                "max_total_score": 250,
                "chart_labels": [
                    "Информационные и медиакомпетенции",
                    "Коммуникация и сотрудничество",
                    "Создание цифрового контента",
                    "Безопасность",
                    "Решение проблем",
                ],
                "level_ranges": {
                    "A2": (10, 20),
                    "B1": (21, 35),
                    "B2": (36, 45),
                    "C1": (46, 50),
                },
                "level_names": {
                    "A2": "Базовый уровень (A2)",
                    "B1": "Средний уровень (B1)",
                    "B2": "Продвинутый уровень (B2)",
                    "C1": "Экспертный уровень (C1)",
                },
                "result_model": DigCompResult,
                "score_fields": [
                    "area1_score",
                    "area2_score",
                    "area3_score",
                    "area4_score",
                    "area5_score",
                ],
            }

        # RIASEC
        elif "riasec" in name or "холланд" in name:
            return {
                "type": "riasec",
                "blocks": 6,
                "questions_per_block": 10,
                "max_score_per_block": 50,
                "max_total_score": 300,
                "chart_labels": [
                    "Реалистичный (R)",
                    "Исследовательский (I)",
                    "Артистический (A)",
                    "Социальный (S)",
                    "Предпринимательский (E)",
                    "Конвенциональный (C)",
                ],
                "level_ranges": {
                    "low": (10, 20),
                    "medium": (21, 35),
                    "high": (36, 50),
                },
                "level_names": {
                    "low": "Низкая склонность",
                    "medium": "Средняя склонность",
                    "high": "Высокая склонность",
                },
                "result_model": RiasacResult,
                "score_fields": [
                    "r_score",
                    "i_score",
                    "a_score",
                    "s_score",
                    "e_score",
                    "c_score",
                ],
            }

        # Big5 (Большая пятёрка)
        elif "big5" in name or "большая пятёрка" in name or "big five" in name:
            return {
                "type": "big5",
                "blocks": 5,
                "questions_per_block": 10,
                "max_score_per_block": 50,
                "max_total_score": 250,
                "chart_labels": [
                    "Экстраверсия",
                    "Доброжелательность",
                    "Добросовестность",
                    "Нейротизм",
                    "Открытость опыту",
                ],
                "level_ranges": {
                    "low": (10, 20),
                    "medium": (21, 35),
                    "high": (36, 50),
                },
                "level_names": {
                    "low": "Низкий уровень",
                    "medium": "Средний уровень",
                    "high": "Высокий уровень",
                },
                "result_model": Big5Result,
                "score_fields": [
                    "extraversion_score",
                    "agreeableness_score",
                    "conscientiousness_score",
                    "neuroticism_score",
                    "openness_score",
                ],
            }

        # Gardner (Множественный интеллект)
        elif (
            "gardner" in name or "гарднер" in name or "множественный интеллект" in name
        ):
            return {
                "type": "gardner",
                "blocks": 8,
                "questions_per_block": 10,
                "max_score_per_block": 50,
                "max_total_score": 400,
                "chart_labels": [
                    "Лингвистический",
                    "Логико-математический",
                    "Пространственный",
                    "Музыкальный",
                    "Телесно-кинестетический",
                    "Межличностный",
                    "Внутриличностный",
                    "Натуралистический",
                ],
                "level_ranges": {
                    "low": (10, 20),
                    "medium": (21, 35),
                    "high": (36, 50),
                },
                "level_names": {
                    "low": "Низкий уровень",
                    "medium": "Средний уровень",
                    "high": "Высокий уровень",
                },
                "result_model": GardnerResult,
                "score_fields": [
                    "linguistic_score",
                    "logical_score",
                    "spatial_score",
                    "musical_score",
                    "kinesthetic_score",
                    "interpersonal_score",
                    "intrapersonal_score",
                    "naturalistic_score",
                ],
            }

        return {
            "type": "custom",
            "blocks": 1,
            "questions_per_block": 0,
            "max_score_per_block": None,
            "max_total_score": None,
            "chart_labels": [],
            "level_ranges": {},
            "level_names": {},
            "result_model": None,
            "score_fields": [],
        }

    @classmethod
    def can_handle(cls, category):
        """Универсальная проверка — обрабатывает все опросы"""
        return True

    # ==================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==================================================================

    def get_level_for_score(self, score, config):
        """Определяет уровень по баллу"""
        for level, (min_score, max_score) in config["level_ranges"].items():
            if min_score <= score <= max_score:
                return level
        return (
            list(config["level_ranges"].keys())[0]
            if config["level_ranges"]
            else "unknown"
        )

    def get_code_for_block(self, block_num):
        """Возвращает код для блока RIASEC"""
        codes = {1: "R", 2: "I", 3: "A", 4: "S", 5: "E", 6: "C"}
        return codes.get(block_num, "")

    def get_interpretation(self, code, user_type="common"):
        """
        Получает интерпретацию из БД.
        Сначала ищет для конкретного user_type, потом для common.
        """
        base_qs = SurveyInterpretation.objects.filter(
            survey_type=self.survey_config["type"],
            code=code,
            is_active=True,
        )

        for ut in (user_type, "common"):
            interpretation = base_qs.filter(user_type=ut).first()
            if interpretation:
                return {
                    "title": interpretation.title,
                    "description": interpretation.description,
                    "recommendations": interpretation.recommendations,
                    "fields": interpretation.fields_list,
                    "color": interpretation.color,
                    "important_notes": interpretation.important_notes,
                }
        return None

    # ==================================================================
    # РАСЧЁТ РЕЗУЛЬТАТОВ
    # ==================================================================

    def calculate_results(self, user_responses):
        """Расчёт результатов опроса"""
        config = self.survey_config

        # Если это пользовательский опрос (custom) - не рассчитываем результаты
        if config["type"] == "custom":
            return None

        questions = (
            SurveyQuestion.objects.filter(block__category=self.category, is_active=True)
            .select_related("block")
            .order_by("block__order", "q_number")
        )

        responses_dict = {}
        for response in user_responses:
            for idx, q in enumerate(questions, start=1):
                if q.id == response.question.id:
                    responses_dict[idx] = response.score
                    break

        block_scores = {}
        for block_num in range(1, config["blocks"] + 1):
            start = (block_num - 1) * config["questions_per_block"] + 1
            end = block_num * config["questions_per_block"]
            scores = [responses_dict.get(q_num, 0) for q_num in range(start, end + 1)]
            block_scores[block_num] = sum(scores)

        # Подготовка данных для сохранения
        defaults_data = {
            field: block_scores[i + 1] for i, field in enumerate(config["score_fields"])
        }

        # Для RIASEC добавляем карьерный код
        if config["type"] == "riasec":
            sorted_scores = sorted(
                block_scores.items(), key=lambda x: x[1], reverse=True
            )
            career_code = "".join(
                [self.get_code_for_block(b) for b, _ in sorted_scores[:3]]
            )
            dominant = ", ".join(
                [f"{self.get_code_for_block(b)}: {s}" for b, s in sorted_scores[:3]]
            )
            defaults_data["career_code"] = career_code
            defaults_data["dominant_types"] = dominant

        result, _ = config["result_model"].objects.update_or_create(
            session=self.session, defaults=defaults_data
        )

        return result

    def get_results(self):
        """
        Возвращает уже сохранённый результат текущей сессии.
        Если результата нет — вернёт None, и views пересчитает через calculate_results.
        """
        config = self.survey_config
        if config["type"] == "custom" or config["result_model"] is None:
            return None
        try:
            return config["result_model"].objects.get(session=self.session)
        except config["result_model"].DoesNotExist:
            return None

    # ==================================================================
    # КОНТЕКСТ ДЛЯ ОТОБРАЖЕНИЯ
    # ==================================================================

    def get_default_recommendations(self, user_type):
        """Стандартные рекомендации, если нет в БД"""
        defaults = {
            (
                "digcomp",
                "employee",
            ): "Определите 1–2 области с наименьшими баллами — начните с них план развития.",
            (
                "digcomp",
                "employer",
            ): "Проведите групповую диагностику для выявления общих зон роста сотрудников.",
            (
                "digcomp",
                "university",
            ): "Адаптируйте содержание курсов под реальные потребности аудитории.",
            ("riasec", "employee"): "Используйте карьерный код для поиска профессий.",
            ("riasec", "employer"): "Используйте опросник для подбора персонала.",
            (
                "riasec",
                "university",
            ): "Адаптируйте учебные программы под склонности студентов.",
        }
        return defaults.get(
            (self.survey_config["type"], user_type),
            "Используйте результаты для планирования развития.",
        )

    def _get_user_education_level(self):
        """
        Возвращает 'VO' / 'SPO' / None на основе EmployeeProfile.
        """
        profile = getattr(self.user, "employee_profile", None)
        if not profile or not profile.education_level:
            return None

        edu = profile.education_level
        if edu in ("higher", "academic_degree"):
            return "VO"
        if edu == "secondary_special":
            return "SPO"
        return None

    def get_results_context(self, results):
        """Контекст для отображения результатов"""
        config = self.survey_config
        user_type = getattr(self.user, "user_type", "common")

        if results is None:
            return {"is_unified": True, "survey_config": config}

        scores = [getattr(results, field) for field in config["score_fields"]]

        # --- Блоки (детальный разбор) ---
        blocks_data = []
        for i, (label, score) in enumerate(zip(config["chart_labels"], scores)):
            level = self.get_level_for_score(score, config)
            interpretation = self.get_interpretation(level, user_type) or {}
            blocks_data.append(
                {
                    "id": i + 1,
                    "name": label,
                    "score": score,
                    "max": config["max_score_per_block"],
                    "level": level,
                    "level_info": {
                        "name": interpretation.get("title", level),
                        "characteristic": interpretation.get("description", ""),
                        "recommendations": interpretation.get("recommendations", ""),
                        "color": interpretation.get("color", "secondary"),
                    },
                }
            )

        # Для RIASEC — сортируем по убыванию баллов
        blocks_data_sorted = (
            sorted(blocks_data, key=lambda x: x["score"], reverse=True)
            if config["type"] == "riasec"
            else blocks_data
        )

        # --- Основная интерпретация и карьерный код ---
        career_code_info = None
        career_guidance = None

        if config["type"] == "riasec":
            main_interpretation = (
                self.get_interpretation(results.career_code, user_type) or {}
            )
            career_code_info = self.get_riasec_code_interpretation(results.career_code)
            career_guidance = self.get_career_guidance(
                results.career_code,
                education_level=self._get_user_education_level(),
            )
        else:
            main_interpretation = self.get_interpretation("common", user_type) or {}

        # --- Общие замечания и рекомендации ---
        common_interpretation = self.get_interpretation("common", user_type) or {}
        important_notes = common_interpretation.get("important_notes", "")

        # Рекомендации по использованию
        usage = self.get_interpretation("usage", user_type) or {}
        if not usage:
            usage = {
                "title": "Рекомендации по использованию результатов",
                "recommendations": self.get_default_recommendations(user_type),
                "description": "Нет плохих результатов — каждый профиль ценен в своей среде.",
            }

        return {
            "is_unified": True,
            "survey_config": config,
            "survey_result": results,
            "blocks_data": blocks_data,
            "blocks_data_sorted": blocks_data_sorted,
            "main_interpretation": main_interpretation,
            "career_code_info": career_code_info,
            "career_guidance": career_guidance,
            "important_notes": important_notes,
            "usage_recommendations": usage,
            "user_type": user_type,
            "user_type_color": (
                "success"
                if user_type == "employee"
                else "info" if user_type == "employer" else "warning"
            ),
            "max_total_score": config["max_total_score"],
            "chart_scores": scores,
        }

    def get_results_template(self):
        return "surveys/survey_results.html"

    # ==================================================================
    # RIASEC-СПЕЦИФИЧНЫЕ МЕТОДЫ
    # ==================================================================

    def get_riasec_code_interpretation(self, career_code):
        """Получает интерпретацию трёхбуквенного кода RIASEC"""
        if not career_code or len(career_code) != 3:
            return None

        try:
            code_obj = RiasecCodeInterpretation.objects.get(
                code=career_code.upper(), is_active=True
            )
        except RiasecCodeInterpretation.DoesNotExist:
            return None

        return {
            "code": code_obj.code,
            "description": code_obj.description,
            "professions": code_obj.professions,
            "professions_list": code_obj.get_professions_list(),
            "dominant_display": code_obj.get_dominant_display(),
            "secondary_display": code_obj.get_secondary_display(),
            "tertiary_display": code_obj.get_tertiary_display(),
        }

    def get_career_guidance(self, career_code, education_level=None):
        """
        Возвращает профстандарты и ФГОС, подходящие под код Холланда.
        ФГОС разделены на ВО и СПО, порядок блоков зависит от education_level.
        """
        if not career_code or len(career_code) != 3:
            return None

        qs = (
            ProfessionalStandard.objects.filter(
                is_active=True, riasec_codes__code=career_code.upper()
            )
            .distinct()
            .prefetch_related(
                Prefetch(
                    "labor_functions",
                    queryset=GeneralizedLaborFunction.objects.filter(
                        is_active=True
                    ).order_by("order", "code"),
                ),
                "program_links__education_program",
                "riasec_codes",
            )
        )

        standards = []
        seen_programs = set()

        vo_programs = []
        spo_programs = []

        # Порядок сортировки: сначала ПС того уровня, что у пользователя
        if education_level == "SPO":
            qs = qs.order_by("education_level", "code")
        else:
            qs = qs.order_by("education_level", "code")

        for ps in qs:
            otf = [
                {
                    "code": f.code,
                    "name": f.name,
                    "qualification_level": f.qualification_level,
                    "order": f.order,
                }
                for f in ps.labor_functions.all()
            ]

            programs = []
            for link in ps.program_links.all().order_by("order"):
                p = link.education_program
                program_data = {
                    "code": p.code,
                    "name": p.name,
                    "education_level": p.education_level,
                    "education_level_display": p.get_education_level_display(),
                    "order": link.order,
                }
                programs.append(program_data)

                key = (p.code, p.name, p.education_level)
                if key not in seen_programs:
                    seen_programs.add(key)
                    if p.education_level == "VO":
                        vo_programs.append(program_data)
                    elif p.education_level == "SPO":
                        spo_programs.append(program_data)

            standards.append(
                {
                    "code": ps.code,
                    "name": ps.name,
                    "education_level": ps.education_level,
                    "education_level_display": ps.get_education_level_display(),
                    "riasec_codes": [r.code for r in ps.riasec_codes.all()],
                    "labor_functions": otf,
                    "programs": programs,
                }
            )

        # --- Порядок блоков ФГОС ---
        # По умолчанию: ВО, потом СПО.
        # Если у пользователя СПО — наоборот: СПО, потом ВО.
        if education_level == "SPO":
            ordered_programs = spo_programs + vo_programs
            programs_order = ["spo", "vo"]
        else:
            ordered_programs = vo_programs + spo_programs
            programs_order = ["vo", "spo"]

        return {
            "career_code": career_code.upper(),
            "standards": standards,
            "vo_programs": vo_programs,
            "spo_programs": spo_programs,
            "vo_programs_count": len(vo_programs),
            "spo_programs_count": len(spo_programs),
            "standards_count": len(standards),
            "programs_order": programs_order,  # ["vo", "spo"] или ["spo", "vo"]
            "ordered_programs": ordered_programs,  # общий отсортированный список
            # Обратная совместимость:
            "top_programs": ordered_programs,
            "programs_count": len(ordered_programs),
        }
