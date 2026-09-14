import json
import logging
import re
import requests
import time
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model

from apps.courses.models import Course
from apps.surveys.models import RiasecCodeInterpretation, SurveyInterpretation
from apps.goal_setting.models import GoalSettingResponse

User = get_user_model()
logger = logging.getLogger(__name__)


class DeepSeekRecommendationService:
    """Сервис для получения рекомендаций через DeepSeek API"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, user):
        self.user = user
        self.api_key = settings.DEEPSEEK_API_KEY

    # ==================================================================
    # ПОЛУЧЕНИЕ СЕССИЙ И ИНТЕРПРЕТАЦИЙ
    # ==================================================================

    def get_latest_completed_session(self, category_name_keyword):
        """Получает последнюю завершённую сессию по ключевому слову в названии категории"""
        return (
            self.user.survey_sessions.filter(
                category__name__icontains=category_name_keyword, status="completed"
            )
            .order_by("-completed_at", "-id")
            .first()
        )

    def get_survey_description(self, survey_type):
        """Получает описание опроса из модели SurveyInterpretation"""
        interpretations = SurveyInterpretation.objects.filter(
            survey_type=survey_type, user_type=self.user.user_type, is_active=True
        ).order_by("order")

        description = []
        for interp in interpretations:
            if interp.description:
                description.append(interp.description)

        return " ".join(description) if description else ""

    def get_survey_interpretation(self, survey_type, code, user_type=None):
        """Получает интерпретацию результатов из БД"""
        if user_type is None:
            user_type = self.user.user_type

        try:
            interpretation = SurveyInterpretation.objects.get(
                survey_type=survey_type, code=code, user_type=user_type, is_active=True
            )
            return {
                "title": interpretation.title,
                "description": interpretation.description,
                "recommendations": interpretation.recommendations,
                "fields": interpretation.fields_list,
                "color": interpretation.color,
            }
        except SurveyInterpretation.DoesNotExist:
            try:
                interpretation = SurveyInterpretation.objects.get(
                    survey_type=survey_type,
                    code=code,
                    user_type="common",
                    is_active=True,
                )
                return {
                    "title": interpretation.title,
                    "description": interpretation.description,
                    "recommendations": interpretation.recommendations,
                    "fields": interpretation.fields_list,
                    "color": interpretation.color,
                }
            except SurveyInterpretation.DoesNotExist:
                return None

    def _get_category_interpretation(self, session):
        """Получает интерпретацию из категории опроса (описание + результат)"""
        if not session or not hasattr(session, "category"):
            return None

        category = session.category
        if not category:
            return None

        full_description = ""

        # Добавляем описание (description)
        if category.description:
            full_description += f"Описание опроса: {category.description}\n\n"

        # Добавляем описание результатов (result_description) без HTML
        clean_result = category.get_result_description_clean()
        if clean_result:
            full_description += f"Описание результатов: {clean_result}"

        if full_description:
            return {
                "description": full_description,
                "recommendations": "",
            }

        return None

    # ==================================================================
    # ЦЕЛЕПОЛАГАНИЕ
    # ==================================================================

    def get_goal_setting_data(self):
        """Получает данные целеполагания пользователя"""
        responses = GoalSettingResponse.objects.filter(user=self.user).select_related(
            "question", "answer_option"
        )

        goal_data = {}
        for response in responses:
            question_text = response.question.text
            if response.answer_option:
                if response.answer_option.is_custom:
                    goal_data[question_text] = response.answer_text
                else:
                    goal_data[question_text] = response.answer_option.label
            elif response.answer_text:
                goal_data[question_text] = response.answer_text
            elif response.answer_date_start and response.answer_date_end:
                goal_data[question_text] = (
                    f"{response.answer_date_start} - {response.answer_date_end}"
                )

        return goal_data

    # ==================================================================
    # ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
    # ==================================================================

    def get_user_profile(self):
        """Собирает полный профиль пользователя из ВСЕХ опросов (берёт последние попытки)"""
        profile = {
            "user_info": {
                "user_type": self.user.user_type,
                "position": None,
                "position_level": None,
                "organization_name": None,
                "organization_industry": None,
                "education_level": None,
                "education_institution": None,
                "graduation_year": None,
                "specialty": None,
                "desired_organization_type": None,
                "desired_organization": None,
                "desired_position": None,
                "is_unemployed": False,
                "is_svo_participant": False,
            },
            "survey_results": {},
            "survey_interpretations": {},
            "has_surveys": False,
        }

        # ========== Информация из профиля работника ==========
        if hasattr(self.user, "employee_profile"):
            emp_profile = self.user.employee_profile

            # Статус занятости
            profile["user_info"]["is_unemployed"] = emp_profile.is_unemployed
            profile["user_info"]["is_svo_participant"] = emp_profile.is_svo_participant

            profile["user_info"]["position"] = emp_profile.position
            profile["user_info"][
                "position_level"
            ] = emp_profile.get_position_level_display()

            if emp_profile.organization:
                profile["user_info"][
                    "organization_name"
                ] = emp_profile.organization.short_name
                if emp_profile.organization.organization_type:
                    profile["user_info"][
                        "organization_industry"
                    ] = emp_profile.organization.organization_type.name

            # Образование
            profile["user_info"]["education_level"] = (
                emp_profile.get_education_level_display()
                if emp_profile.education_level
                else None
            )
            profile["user_info"][
                "education_institution"
            ] = emp_profile.education_institution
            profile["user_info"]["graduation_year"] = emp_profile.graduation_year
            profile["user_info"]["specialty"] = emp_profile.specialty

            # Желаемая сфера/организация/должность
            if emp_profile.desired_organization_type:
                profile["user_info"][
                    "desired_organization_type"
                ] = emp_profile.desired_organization_type.name
            profile["user_info"][
                "desired_organization"
            ] = emp_profile.desired_organization
            profile["user_info"]["desired_position"] = emp_profile.desired_position

        # ========== Результаты RIASEC ==========
        riasec_session = self.get_latest_completed_session("Холланд")
        if riasec_session and hasattr(riasec_session, "riasac_result"):
            r = riasec_session.riasac_result
            profile["has_surveys"] = True

            riasec_data = {
                "career_code": r.career_code,
                "scores": {
                    "Реалистичный (R)": r.r_score,
                    "Исследовательский (I)": r.i_score,
                    "Артистический (A)": r.a_score,
                    "Социальный (S)": r.s_score,
                    "Предпринимательский (E)": r.e_score,
                    "Конвенциональный (C)": r.c_score,
                },
            }

            # Добавляем интерпретацию кода из RiasecCodeInterpretation
            if r.career_code:
                try:
                    code_interp = RiasecCodeInterpretation.objects.get(
                        code=r.career_code.upper(), is_active=True
                    )
                    riasec_data["code_description"] = code_interp.description
                    riasec_data["professions"] = code_interp.get_professions_list()
                    riasec_data["dominant"] = code_interp.get_dominant_display()
                    riasec_data["secondary"] = code_interp.get_secondary_display()
                    riasec_data["tertiary"] = code_interp.get_tertiary_display()
                except RiasecCodeInterpretation.DoesNotExist:
                    logger.warning(
                        f"RiasecCodeInterpretation не найден для кода {r.career_code}"
                    )

            profile["survey_results"]["riasec"] = riasec_data

            interpretation = self._get_category_interpretation(riasec_session)
            if interpretation:
                profile["survey_interpretations"]["riasec"] = interpretation

        # ========== Результаты DigComp ==========
        digcomp_session = self.get_latest_completed_session("DigComp")
        if digcomp_session and hasattr(digcomp_session, "digcomp_result"):
            d = digcomp_session.digcomp_result
            profile["has_surveys"] = True

            profile["survey_results"]["digcomp"] = {
                "scores": {
                    "Профессиональное вовлечение": d.area1_score,
                    "Цифровые ресурсы": d.area2_score,
                    "Обучение и преподавание": d.area3_score,
                    "Оценивание": d.area4_score,
                    "Расширение прав": d.area5_score,
                }
            }

            interpretation = self._get_category_interpretation(digcomp_session)
            if interpretation:
                profile["survey_interpretations"]["digcomp"] = interpretation

        # ========== Результаты Big5 ==========
        big5_session = self.get_latest_completed_session("Большая пятёрка")
        if big5_session and hasattr(big5_session, "big5_result"):
            b = big5_session.big5_result
            profile["has_surveys"] = True

            profile["survey_results"]["big5"] = {
                "scores": {
                    "Экстраверсия": b.extraversion_score,
                    "Доброжелательность": b.agreeableness_score,
                    "Добросовестность": b.conscientiousness_score,
                    "Нейротизм": b.neuroticism_score,
                    "Открытость опыту": b.openness_score,
                }
            }

            interpretation = self._get_category_interpretation(big5_session)
            if interpretation:
                profile["survey_interpretations"]["big5"] = interpretation

        # ========== Результаты Гарднера ==========
        gardner_session = self.get_latest_completed_session("Гарднер")
        if gardner_session and hasattr(gardner_session, "gardner_result"):
            g = gardner_session.gardner_result
            profile["has_surveys"] = True

            profile["survey_results"]["gardner"] = {
                "scores": {
                    "Лингвистический": g.linguistic_score,
                    "Логико-математический": g.logical_score,
                    "Пространственный": g.spatial_score,
                    "Музыкальный": g.musical_score,
                    "Телесно-кинестетический": g.kinesthetic_score,
                    "Межличностный": g.interpersonal_score,
                    "Внутриличностный": g.intrapersonal_score,
                    "Натуралистический": g.naturalistic_score,
                }
            }

            interpretation = self._get_category_interpretation(gardner_session)
            if interpretation:
                profile["survey_interpretations"]["gardner"] = interpretation

        return profile

    # ==================================================================
    # КУРСЫ
    # ==================================================================

    def get_courses_for_ai(self):
        """Получает ВСЕ активные курсы для отправки в AI"""
        return Course.objects.filter(is_deleted=False).distinct()

    def _build_courses_list(self, courses):
        """Формирует список курсов для промпта с сокращёнными полями."""
        courses_list = []
        for course in courses:
            categories = ", ".join([cat.name for cat in course.categories.all()])

            # Сокращаем description до 150 символов
            desc = course.description or ""
            if len(desc) > 150:
                desc = desc[:150] + "..."

            # Сокращаем target_audience до 80 символов
            audience = course.target_audience or ""
            if len(audience) > 80:
                audience = audience[:80] + "..."

            courses_list.append(
                {
                    "id": course.id,
                    "title": course.title,
                    "description": desc,
                    "categories": categories,
                    "program_type": course.program_type,
                    "duration_hours": course.duration_hours,
                    "format": course.format,
                    "target_audience": audience,
                    "start_dates": course.start_dates or "Не указана",
                }
            )
        return courses_list

    # ==================================================================
    # ПОДГОТОВКА ПРОМПТА
    # ==================================================================

    def prepare_prompt(
        self, user_profile, goal_data, courses_batch=None, batch_info=None
    ):
        """
        Подготавливает промпт для DeepSeek.

        Args:
            user_profile: готовый профиль пользователя (из get_user_profile).
            goal_data: готовые данные целеполагания (из get_goal_setting_data).
            courses_batch: список курсов для этой партии (если None — берутся все).
            batch_info: dict с ключами "current" и "total" — номер партии и всего партий.
        """
        if courses_batch is None:
            courses_batch = list(self.get_courses_for_ai())

        # Получаем сегодняшнюю дату
        today = date.today()
        today_str = today.strftime("%d.%m.%Y")

        # Формируем список курсов с сокращёнными полями
        courses_list = self._build_courses_list(courses_batch)

        # Формируем интерпретации для промпта
        riasec = user_profile.get("survey_results", {}).get("riasec", {})
        riasec_interp = user_profile.get("survey_interpretations", {}).get("riasec", {})
        digcomp_interp = user_profile.get("survey_interpretations", {}).get(
            "digcomp", {}
        )
        big5_interp = user_profile.get("survey_interpretations", {}).get("big5", {})
        gardner_interp = user_profile.get("survey_interpretations", {}).get(
            "gardner", {}
        )

        has_surveys = user_profile.get("has_surveys", False)
        is_unemployed = user_profile["user_info"].get("is_unemployed", False)
        is_svo = user_profile["user_info"].get("is_svo_participant", False)

        # ========== Блок статуса занятости ==========
        if is_unemployed:
            employment_status_text = "Безработный"
            if is_svo:
                employment_status_text += " (участник СВО)"
            position_text = "Безработный"
            position_level_text = "—"
            organization_text = "Безработный (нет организации)"
            industry_text = "—"
        else:
            employment_status_text = "Работающий"
            if is_svo:
                employment_status_text += " (участник СВО)"
            position_text = user_profile["user_info"]["position"] or "Не указана"
            position_level_text = (
                user_profile["user_info"]["position_level"] or "Не указан"
            )
            organization_text = (
                user_profile["user_info"]["organization_name"] or "Не указана"
            )
            industry_text = (
                user_profile["user_info"]["organization_industry"] or "Не указана"
            )

        # ========== Дополнительная информация из профиля ==========
        extra_info = ""
        if user_profile["user_info"].get("education_level"):
            extra_info += (
                f"Уровень образования: {user_profile['user_info']['education_level']}\n"
            )
        if user_profile["user_info"].get("education_institution"):
            extra_info += f"Учебное заведение: {user_profile['user_info']['education_institution']}\n"
        if user_profile["user_info"].get("graduation_year"):
            extra_info += (
                f"Год окончания: {user_profile['user_info']['graduation_year']}\n"
            )
        if user_profile["user_info"].get("specialty"):
            extra_info += f"Специальность: {user_profile['user_info']['specialty']}\n"
        if user_profile["user_info"].get("desired_organization_type"):
            extra_info += f"Желаемая сфера: {user_profile['user_info']['desired_organization_type']}\n"
        if user_profile["user_info"].get("desired_organization"):
            extra_info += f"Желаемая организация: {user_profile['user_info']['desired_organization']}\n"
        if user_profile["user_info"].get("desired_position"):
            extra_info += (
                f"Желаемая должность: {user_profile['user_info']['desired_position']}\n"
            )

        if extra_info:
            extra_info = f"\n## ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ИЗ ПРОФИЛЯ\n{extra_info}"

        # ========== Секция целеполагания ==========
        goal_section = ""
        if goal_data:
            goal_text = ""
            for question, answer in goal_data.items():
                goal_text += f"- {question}: {answer}\n"
            goal_section = f"""
## ЦЕЛЕПОЛАГАНИЕ (ответы пользователя)
{goal_text}"""

        # ========== Секция результатов тестов ==========
        surveys_section = ""
        if has_surveys:
            surveys_section = f"""
## РЕЗУЛЬТАТЫ ТЕСТОВ

### RIASEC / Холланд (профессиональные склонности)
Карьерный код: {riasec.get('career_code', 'Не определен')}
Баллы: {json.dumps(riasec.get('scores', {}), ensure_ascii=False)}

**Расшифровка кода:**
{riasec.get('code_description', 'Нет описания')}

**Доминирующие типы:**
- Ведущий: {riasec.get('dominant', '—')}
- Дополнительный: {riasec.get('secondary', '—')}
- Поддерживающий: {riasec.get('tertiary', '—')}

**Подходящие профессии:**
{', '.join(riasec.get('professions') or []) or 'Не указаны'}

**Интерпретация:**
{riasec_interp.get('description', 'Нет описания')}

### Цифровая грамотность (DigCompEdu)
Баллы: {json.dumps(user_profile['survey_results'].get('digcomp', {}).get('scores', {}), ensure_ascii=False)}

**Интерпретация:**
{digcomp_interp.get('description', 'Нет описания')}

### Большая пятёрка (личностные черты)
Баллы: {json.dumps(user_profile['survey_results'].get('big5', {}).get('scores', {}), ensure_ascii=False)}

**Интерпретация:**
{big5_interp.get('description', 'Нет описания')}

### Множественный интеллект (Гарднер)
Баллы: {json.dumps(user_profile['survey_results'].get('gardner', {}).get('scores', {}), ensure_ascii=False)}

**Интерпретация:**
{gardner_interp.get('description', 'Нет описания')}"""
        else:
            surveys_section = """
## РЕЗУЛЬТАТЫ ТЕСТОВ
Пользователь ещё не проходил опросы. Используй только информацию из профиля для подбора курсов."""

        # ========== Секция для безработных ==========
        if is_unemployed:
            unemployed_section = """
**ОСОБЕННОСТИ ДЛЯ БЕЗРАБОТНЫХ:**
- **Учитывай** желаемую сферу, желаемую организацию и желаемую должность (они есть в профиле).
- **Учитывай** уровень образования, специальность и год окончания.
- **Учитывай** целеполагание — для безработных это ОСОБЕННО ВАЖНО, так как именно цели определяют, какие курсы помогут найти работу.
- Если пользователь участник СВО — учитывай это как дополнительный контекст (возможно, есть специфические программы поддержки).
"""
        else:
            unemployed_section = ""

        # ========== Секция батча (если это часть) ==========
        batch_section = ""
        if batch_info:
            current = batch_info.get("current", 1)
            total = batch_info.get("total", 1)
            batch_section = f"""
**ВАЖНО: ЭТО ПАРТИЯ {current} ИЗ {total}.**
Ты видишь только часть курсов. Оценивай только те курсы, которые есть в этой партии.
Не пытайся угадать курсы из других партий.
"""

        # ========== Формируем промпт ==========
        prompt = f"""
Ты - эксперт по подбору образовательных курсов.

## ТЕКУЩАЯ ДАТА
Сегодня: {today_str}

## ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ

Тип: {user_profile['user_info']['user_type']}
Статус занятости: {employment_status_text}
Должность: {position_text}
Уровень должности: {position_level_text}
Организация: {organization_text}
Сфера деятельности: {industry_text}
{extra_info}
{goal_section}
{surveys_section}

## ДОСТУПНЫЕ КУРСЫ
{json.dumps(courses_list, ensure_ascii=False, indent=2)}
{batch_section}
## ЗАДАНИЕ
На основе профиля пользователя (обязательно), целеполагания (обязательно) и результатов тестов (если есть), выбери ВСЕ подходящие курсы с оценкой 50% и выше.

{unemployed_section}
**ВАЖНОЕ ПРАВИЛО ПО ДАТАМ:**
- У каждого курса может быть указана дата начала (поле start_dates)
- Если дата начала указана, проверь: не начался ли уже курс
- Сравни дату начала с сегодняшней датой ({today_str})
- Если дата начала уже прошла - НЕ РЕКОМЕНДУЙ такой курс (исключи его из рекомендаций)
- Если дата начала в будущем или сегодня - курс можно рекомендовать
- Если дата начала не указана ("Не указана") - просто игнорируй это поле, рекомендация возможна

**ПРАВИЛА УЧЁТА ЦЕЛЕПОЛАГАНИЯ:**
- **Желаемая форма обучения** — учитывай, НО только если у курса указан формат (поле format). Если формат курса не указан — не исключай курс, просто оценивай по другим критериям.
- **Желаемый период обучения** — учитывай, НО только если у курса есть конкретные даты или периоды набора (поле start_dates). Если даты не указаны — не исключай курс, период не является обязательным условием.

**ПРАВИЛА ОЦЕНКИ:**
- 95-100: Идеальное совпадение
- 80-94: Отличное совпадение
- 65-79: Хорошее совпадение
- 50-64: Удовлетворительное

**ВАЖНО:**
- Учитывай должность, уровень, организацию пользователя (если он работающий)
- **ОБЯЗАТЕЛЬНО** учитывай целеполагание пользователя (причины обучения, желаемые результаты, ключевые слова)
- Если есть результаты тестов, используй их для более точного подбора
- Если тестов нет, подбирай курсы на основе профиля и целеполагания
- **ОБЯЗАТЕЛЬНО** учитывай расшифровку карьерного кода RIASEC и список подходящих профессий при подборе курсов, если есть
- **ОБЯЗАТЕЛЬНО** проверяй даты начала курсов и исключай те, которые уже начались
- Учитывай образование пользователя (если указано)
- Учитывай желаемую сферу/организацию/должность (если указаны) — **для безработных это ключевой критерий**

**ОГРАНИЧЕНИЯ:**
- Максимальное количество рекомендаций: НЕ БОЛЕЕ 90 курсов.
- Если подходит больше 90 курсов, выбери 90 САМЫХ РЕЛЕВАНТНЫХ.
- Если подходит меньше 90, выдай все подходящие.
- **НЕ ДУБЛИРУЙ КУРСЫ** — каждый курс должен быть указан только один раз.

**ФОРМАТ ПРИЧИНЫ РЕКОМЕНДАЦИИ:**
- НЕ ПОВТОРЯЙ название курса в причине.
- Начинай причину со слов: "Этот курс..." или "Программа..." или сразу с описания пользы.
- КАЖДУЮ ПРИЧИНУ ДЕЛАЙ КРАТКОЙ (1-2 предложения), не более 50 слов.

Для каждого курса укажи:
1. ID курса
2. Причину рекомендации (2-3 предложения, используя профиль и интерпретации результатов)
3. Оценку релевантности (целое число от 50 до 100)

Верни ответ строго в формате JSON без дополнительных пояснений:
{{"recommendations": [{{"course_id": 123, "reason": "Текст причины...", "relevance_score": 85}}]}}

ЕСЛИ НЕТ ПОДХОДЯЩИХ КУРСОВ, верни {{"recommendations": []}} (пустой массив).
"""

        # Логирование размера промпта
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 2.5
        batch_str = (
            f" (партия {batch_info['current']}/{batch_info['total']})"
            if batch_info
            else ""
        )
        logger.info(
            f"Промпт{batch_str}: {prompt_length} символов, "
            f"~{estimated_tokens:.0f} токенов, курсов: {len(courses_list)}"
        )

        return prompt

    # ==================================================================
    # ПОЛУЧЕНИЕ РЕКОМЕНДАЦИЙ (батчами)
    # ==================================================================

    def get_recommendations(self):
        """Получает рекомендации от DeepSeek API, разбивая курсы на батчи."""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не настроен")

        all_courses = list(self.get_courses_for_ai())
        total_courses = len(all_courses)

        if total_courses == 0:
            logger.warning("Нет активных курсов для рекомендаций")
            return []

        # Размер батча — подбираем так, чтобы промпт укладывался в лимит токенов.
        # ~150 курсов дают ~35-40K токенов — с запасом до 64K.
        BATCH_SIZE = 150
        batches = [
            all_courses[i : i + BATCH_SIZE] for i in range(0, total_courses, BATCH_SIZE)
        ]
        total_batches = len(batches)

        logger.info(
            f"Рекомендации: {total_courses} курсов, разбито на {total_batches} "
            f"батчей по {BATCH_SIZE}"
        )

        # Собираем профиль и целеполагание ОДИН РАЗ (а не для каждого батча)
        user_profile = self.get_user_profile()
        goal_data = self.get_goal_setting_data()

        # Множество валидных ID курсов — для проверки ответа AI
        valid_course_ids = {c.id for c in all_courses}

        all_recommendations = []

        for idx, batch in enumerate(batches, 1):
            batch_info = {"current": idx, "total": total_batches}
            logger.info(f"Обработка батча {idx}/{total_batches} ({len(batch)} курсов)")

            try:
                prompt = self.prepare_prompt(
                    user_profile=user_profile,
                    goal_data=goal_data,
                    courses_batch=batch,
                    batch_info=batch_info,
                )
                recommendations = self._call_deepseek_api(prompt)
                all_recommendations.extend(recommendations)
                logger.info(
                    f"Батч {idx}/{total_batches}: получено "
                    f"{len(recommendations)} рекомендаций"
                )
            except Exception as e:
                logger.error(f"Ошибка при обработке батча {idx}/{total_batches}: {e}")
                # Продолжаем со следующим батчем, не роняя всю задачу
                continue

        # Дедупликация по course_id + валидация
        seen_ids = set()
        unique_recommendations = []
        invalid_count = 0
        for rec in all_recommendations:
            course_id = rec.get("course_id")
            if course_id is None:
                continue
            # Проверяем, что курс существует
            if course_id not in valid_course_ids:
                invalid_count += 1
                logger.warning(f"AI вернул несуществующий course_id: {course_id}")
                continue
            if course_id in seen_ids:
                continue
            seen_ids.add(course_id)
            unique_recommendations.append(rec)

        if invalid_count:
            logger.warning(f"Отброшено невалидных course_id: {invalid_count}")

        # Сортировка по релевантности (по убыванию)
        unique_recommendations.sort(
            key=lambda r: r.get("relevance_score", 0), reverse=True
        )

        # Ограничиваем 90 курсами
        MAX_RECOMMENDATIONS = 90
        if len(unique_recommendations) > MAX_RECOMMENDATIONS:
            unique_recommendations = unique_recommendations[:MAX_RECOMMENDATIONS]

        logger.info(
            f"Итого рекомендаций: {len(unique_recommendations)} "
            f"(из {len(all_recommendations)} до дедупликации)"
        )

        return unique_recommendations

    # ==================================================================
    # ВЫЗОВ DEEPSEEK API
    # ==================================================================

    def _call_deepseek_api(self, prompt):
        """Отправляет промпт в DeepSeek и возвращает список рекомендаций."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Ты эксперт по подбору образовательных курсов. "
                        "Отвечай ТОЛЬКО в формате JSON, без дополнительного текста, "
                        "пояснений или форматирования. Не используй markdown, "
                        "не добавляй комментарии. Ответ должен начинаться с { "
                        "и заканчиваться }."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 64000,
        }

        content = ""
        try:
            response = requests.post(
                self.API_URL, headers=headers, json=data, timeout=180
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            recommendations_data = self._extract_json_from_response(content)

            if not recommendations_data or not recommendations_data.get(
                "recommendations"
            ):
                logger.warning("Не удалось извлечь рекомендации из ответа AI")
                return []

            recommendations = recommendations_data.get("recommendations", [])

            # Нормализация оценки
            for rec in recommendations:
                score = rec.get("relevance_score", 0)
                if isinstance(score, (int, float)):
                    if 0 <= score <= 1:
                        rec["relevance_score"] = round(score * 100)
                    else:
                        rec["relevance_score"] = round(score)
                else:
                    rec["relevance_score"] = 0

                rec["relevance_score"] = max(0, min(100, rec["relevance_score"]))

            return recommendations

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Content: {content[:1000]}...")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    # ==================================================================
    # ИЗВЛЕЧЕНИЕ JSON ИЗ ОТВЕТА AI
    # ==================================================================

    def _extract_json_from_response(self, content):
        """
        Извлекает JSON из ответа AI.
        Пытается найти JSON даже если есть лишний текст.
        """
        if not content:
            logger.warning("Пустой ответ от AI")
            return {"recommendations": []}

        # 1. Пробуем распарсить как есть
        try:
            data = json.loads(content)
            if "recommendations" in data:
                return data
        except json.JSONDecodeError as e:
            logger.debug(f"Прямой парсинг не удался: {e}")

        # 2. Ищем JSON с помощью регулярного выражения
        json_pattern = r'\{[^{}]*"recommendations"[^{}]*\{[^{}]*\}[^{}]*\}'

        if not re.search(json_pattern, content, re.DOTALL):
            json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"

        matches = re.findall(json_pattern, content, re.DOTALL)

        for match in matches:
            try:
                cleaned = re.sub(r",\s*}", "}", match)
                cleaned = re.sub(r",\s*]", "]", cleaned)
                data = json.loads(cleaned)
                if "recommendations" in data:
                    logger.info("JSON успешно извлечён из ответа")
                    return data
            except json.JSONDecodeError:
                continue

        # 3. Пробуем найти по ключевым словам
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and start < end:
            json_str = content[start : end + 1]
            try:
                json_str = re.sub(r",\s*}", "}", json_str)
                json_str = re.sub(r",\s*]", "]", json_str)
                data = json.loads(json_str)
                if "recommendations" in data:
                    logger.info("JSON успешно извлечён с очисткой от trailing commas")
                    return data
            except json.JSONDecodeError as e:
                logger.debug(f"Парсинг с очисткой не удался: {e}")

        # 4. Пробуем разбить на части
        try:
            pattern = r'(\{"recommendations":\s*\[.*?\])'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                if "recommendations" in data:
                    logger.info("JSON успешно извлечён через поиск по шаблону")
                    return data
        except (json.JSONDecodeError, AttributeError):
            pass

        # 5. Если ничего не помогло
        logger.error("Не удалось извлечь JSON из ответа")
        logger.debug(f"Содержимое ответа (первые 1000 символов): {content[:1000]}...")
        logger.debug(f"Содержимое ответа (последние 500 символов): {content[-500:]}...")

        return {"recommendations": []}
