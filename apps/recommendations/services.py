import json
import requests
from django.conf import settings
from django.db.models import Q
from django.contrib.auth import get_user_model

from apps.courses.models import Course
from apps.surveys.models import SurveyInterpretation

User = get_user_model()


class DeepSeekRecommendationService:
    """Сервис для получения рекомендаций через DeepSeek API"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, user):
        self.user = user
        self.api_key = settings.DEEPSEEK_API_KEY

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
            # Пробуем common
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

    def get_user_profile(self):
        """Собирает полный профиль пользователя из ВСЕХ опросов (берёт последние попытки)"""
        profile = {
            "user_info": {
                "user_type": self.user.user_type,
                "position": None,
                "position_level": None,
                "organization_name": None,
                "organization_industry": None,
            },
            "survey_results": {},
            "survey_interpretations": {},
        }

        # ========== Информация из профиля работника ==========
        if hasattr(self.user, "employee_profile"):
            emp_profile = self.user.employee_profile
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

        # ========== Результаты RIASEC ==========
        riasec_session = self.get_latest_completed_session("Холланд")
        if riasec_session and hasattr(riasec_session, "riasac_result"):
            r = riasec_session.riasac_result

            # Получаем интерпретацию карьерного кода
            interpretation = self.get_survey_interpretation("riasec", r.career_code)

            profile["survey_results"]["riasec"] = {
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

            # Сохраняем интерпретацию отдельно
            if interpretation:
                profile["survey_interpretations"]["riasec"] = {
                    "title": interpretation.get("title", ""),
                    "description": interpretation.get("description", ""),
                    "recommendations": interpretation.get("recommendations", ""),
                    "suitable_fields": interpretation.get("fields", ""),
                }

        # ========== Результаты DigComp ==========
        digcomp_session = self.get_latest_completed_session("DigComp")
        if digcomp_session and hasattr(digcomp_session, "digcomp_result"):
            d = digcomp_session.digcomp_result

            profile["survey_results"]["digcomp"] = {
                "scores": {
                    "Профессиональное вовлечение": d.area1_score,
                    "Цифровые ресурсы": d.area2_score,
                    "Обучение и преподавание": d.area3_score,
                    "Оценивание": d.area4_score,
                    "Расширение прав": d.area5_score,
                }
            }

            # Получаем общую интерпретацию для DigComp
            interpretation = self.get_survey_interpretation("digcomp", "common")
            if interpretation:
                profile["survey_interpretations"]["digcomp"] = {
                    "description": interpretation.get("description", ""),
                    "recommendations": interpretation.get("recommendations", ""),
                }

        # ========== Результаты Big5 ==========
        big5_session = self.get_latest_completed_session("Большая пятёрка")
        if big5_session and hasattr(big5_session, "big5_result"):
            b = big5_session.big5_result

            profile["survey_results"]["big5"] = {
                "scores": {
                    "Экстраверсия": b.extraversion_score,
                    "Доброжелательность": b.agreeableness_score,
                    "Добросовестность": b.conscientiousness_score,
                    "Нейротизм": b.neuroticism_score,
                    "Открытость опыту": b.openness_score,
                }
            }

            # Получаем общую интерпретацию для Big5
            interpretation = self.get_survey_interpretation("big5", "common")
            if interpretation:
                profile["survey_interpretations"]["big5"] = {
                    "description": interpretation.get("description", ""),
                    "recommendations": interpretation.get("recommendations", ""),
                }

        # ========== Результаты Гарднера ==========
        gardner_session = self.get_latest_completed_session("Множественный интеллект")
        if gardner_session and hasattr(gardner_session, "gardner_result"):
            g = gardner_session.gardner_result

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

            # Получаем общую интерпретацию для Гарднера
            interpretation = self.get_survey_interpretation("gardner", "common")
            if interpretation:
                profile["survey_interpretations"]["gardner"] = {
                    "description": interpretation.get("description", ""),
                    "recommendations": interpretation.get("recommendations", ""),
                }

        return profile

    def get_courses_for_ai(self, limit=50):
        """Получает курсы для отправки в AI (с предварительной фильтрацией)"""
        # Предварительная фильтрация: активные курсы
        queryset = Course.objects.filter(is_deleted=False)

        # Фильтр по категориям на основе профиля
        user_profile = self.get_user_profile()

        # Если есть RIASEC код, фильтруем курсы по категориям
        riasec_code = (
            user_profile.get("survey_results", {})
            .get("riasec", {})
            .get("career_code", "")
        )
        if riasec_code:
            # Сопоставление RIASEC кодов с категориями курсов
            riasec_keywords = {
                "R": ["инженерия", "техника", "строительство", "механика"],
                "I": ["наука", "исследование", "анализ", "данные", "лаборатория"],
                "A": ["дизайн", "творчество", "искусство", "мультимедиа"],
                "S": ["обучение", "консультирование", "педагогика", "социальный"],
                "E": ["бизнес", "управление", "менеджмент", "предпринимательство"],
                "C": ["бухгалтерия", "администрирование", "документация", "офис"],
            }

            # Собираем ключевые слова для поиска
            keywords = []
            for letter in riasec_code[:3]:  # Берём первые 3 буквы кода
                keywords.extend(riasec_keywords.get(letter, []))

            if keywords:
                # Строим Q объект для поиска по категориям и описанию
                q_filter = Q()
                for kw in keywords:
                    q_filter |= Q(categories__name__icontains=kw)
                    q_filter |= Q(title__icontains=kw)
                    q_filter |= Q(description__icontains=kw)
                queryset = queryset.filter(q_filter)

        # Ограничиваем количество курсов для AI (не более 50)
        return queryset.distinct()[:limit]

    def prepare_prompt(self):
        """Подготавливает промпт для DeepSeek"""
        user_profile = self.get_user_profile()
        courses = self.get_courses_for_ai()

        courses_list = []
        for course in courses:
            categories = ", ".join([cat.name for cat in course.categories.all()])
            courses_list.append(
                {
                    "id": course.id,
                    "title": course.title,
                    "description": (
                        course.description[:500] if course.description else ""
                    ),
                    "categories": categories,
                    "program_type": course.program_type,
                    "duration_hours": course.duration_hours,
                    "study_mode": course.study_mode,
                    "format": course.format,
                    "target_audience": (
                        course.target_audience[:200] if course.target_audience else ""
                    ),
                    "document_type": course.document_type,
                    "price": course.price,
                }
            )

        # Формируем интерпретации для промпта
        riasec_interp = user_profile.get("survey_interpretations", {}).get("riasec", {})
        digcomp_interp = user_profile.get("survey_interpretations", {}).get(
            "digcomp", {}
        )
        big5_interp = user_profile.get("survey_interpretations", {}).get("big5", {})
        gardner_interp = user_profile.get("survey_interpretations", {}).get(
            "gardner", {}
        )

        prompt = f"""
            Ты - эксперт по подбору образовательных курсов в сфере IT и искусственного интеллекта.

            ## ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ

            Тип: {user_profile['user_info']['user_type']}
            Должность: {user_profile['user_info']['position'] or 'Не указана'}
            Организация: {user_profile['user_info']['organization_name'] or 'Не указана'}
            Сфера деятельности: {user_profile['user_info']['organization_industry'] or 'Не указана'}

            ## РЕЗУЛЬТАТЫ ТЕСТОВ

            ### RIASEC / Холланд (профессиональные склонности)
            Карьерный код: {user_profile['survey_results'].get('riasec', {}).get('career_code', 'Не определен')}
            Баллы: {json.dumps(user_profile['survey_results'].get('riasec', {}).get('scores', {}), ensure_ascii=False)}

            **Интерпретация:**
            - Описание: {riasec_interp.get('description', '')}
            - Рекомендации: {riasec_interp.get('recommendations', '')}
            - Подходящие сферы: {riasec_interp.get('suitable_fields', '')}

            ### Цифровая грамотность (DigCompEdu)
            Баллы: {json.dumps(user_profile['survey_results'].get('digcomp', {}).get('scores', {}), ensure_ascii=False)}

            **Интерпретация:**
            - Описание: {digcomp_interp.get('description', '')}
            - Рекомендации: {digcomp_interp.get('recommendations', '')}

            ### Большая пятёрка (личностные черты)
            Баллы: {json.dumps(user_profile['survey_results'].get('big5', {}).get('scores', {}), ensure_ascii=False)}

            **Интерпретация:**
            - Описание: {big5_interp.get('description', '')}
            - Рекомендации: {big5_interp.get('recommendations', '')}

            ### Множественный интеллект (Гарднер)
            Баллы: {json.dumps(user_profile['survey_results'].get('gardner', {}).get('scores', {}), ensure_ascii=False)}

            **Интерпретация:**
            - Описание: {gardner_interp.get('description', '')}
            - Рекомендации: {gardner_interp.get('recommendations', '')}

            ## ДОСТУПНЫЕ КУРСЫ
            {json.dumps(courses_list, ensure_ascii=False, indent=2)}

            ## ЗАДАНИЕ
            На основе профиля пользователя, выбери ВСЕ подходящие курсы с оценкой 50% и выше.

            **ПРАВИЛА ОЦЕНКИ:**
            - 95-100: Идеальное совпадение
            - 80-94: Отличное совпадение
            - 65-79: Хорошее совпадение
            - 50-64: Удовлетворительное

            ВКЛЮЧАЙ В ОТВЕТ ВСЕ КУРСЫ С ОЦЕНКОЙ 50% И ВЫШЕ!

            Для каждого курса укажи:
            1. ID курса
            2. Причину рекомендации (2-3 предложения, используя интерпретации результатов)
            3. Оценку релевантности (целое число от 50 до 100)

            Верни ответ строго в формате JSON:
            {{
            "recommendations": [
                {{
                "course_id": 123,
                "reason": "Текст причины...",
                "relevance_score": 85
                }}
            ]
            }}
        """

        return prompt

    def get_recommendations(self):
        """Получает рекомендации от DeepSeek API"""
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не настроен")

        prompt = self.prepare_prompt()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты эксперт по подбору образовательных курсов. Отвечай только в формате JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(
                self.API_URL, headers=headers, json=data, timeout=60
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Парсим JSON ответ
            recommendations_data = json.loads(content)
            recommendations = recommendations_data.get("recommendations", [])

            # Преобразуем оценки в проценты
            for rec in recommendations:
                score = rec.get("relevance_score", 0)

                if isinstance(score, (int, float)):
                    # Если оценка от 0 до 1 (старый формат)
                    if score <= 1:
                        rec["relevance_score"] = round(score * 100)
                    # Если оценка уже от 0 до 100, округляем
                    else:
                        rec["relevance_score"] = round(score)
                else:
                    rec["relevance_score"] = 0

                # Гарантируем, что оценка не выходит за пределы 0-100
                rec["relevance_score"] = max(0, min(100, rec["relevance_score"]))

            return recommendations

        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API error: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            raise
