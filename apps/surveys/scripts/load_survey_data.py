#!/usr/bin/env python
"""Скрипт для загрузки интерпретаций опросов в БД"""

import os
import sys

# Добавляем путь к проекту (корневая директория)
BASE_DIR = "/App"
sys.path.insert(0, BASE_DIR)

# Указываем настройки проекта
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai.settings")

# Инициализируем Django
import django

django.setup()

from apps.surveys.models import SurveyInterpretation

# ============================================================
# Уровни для DigCompEdu
# ============================================================
DIGCOMP_DATA = {
    "levels": {
        "A2": {
            "title": "Базовый уровень (A2)",
            "description": "Умеет выполнять базовые операции, но испытывает трудности с новыми задачами",
            "recommendations": "Пройти вводные курсы по цифровой грамотности",
            "color": "success",
        },
        "B1": {
            "title": "Средний уровень (B1)",
            "description": "Уверенно пользуется распространёнными инструментами",
            "recommendations": "Изучить продвинутые функции",
            "color": "info",
        },
        "B2": {
            "title": "Продвинутый уровень (B2)",
            "description": "Эффективно применяет технологии",
            "recommendations": "Участвовать в онлайнсообществах",
            "color": "warning",
        },
        "C1": {
            "title": "Экспертный уровень (C1)",
            "description": "Творчески использует технологии",
            "recommendations": "Менторить начинающих",
            "color": "danger",
        },
    },
}

# ============================================================
# Уровни для RIASEC
# ============================================================
RIASEC_DATA = {
    "levels": {
        "low": {
            "title": "Низкая склонность",
            "description": "Выраженность типа ниже среднего",
            "color": "secondary",
        },
        "medium": {
            "title": "Средняя склонность",
            "description": "Умеренная выраженность типа",
            "color": "info",
        },
        "high": {
            "title": "Высокая склонность",
            "description": "Сильная выраженность типа",
            "color": "success",
        },
    },
    "important_notes": """
<ul class="list-group list-group-flush">
    <li class="list-group-item">Нет «плохих» типов: каждый тип ценен в своей среде и выполняет важные функции.</li>
    <li class="list-group-item">Гибкость: склонности могут развиваться — вы можете усилить слабые стороны через обучение и практику.</li>
    <li class="list-group-item">Контекст: одна и та же профессия может требовать разных типов в разных организациях (например, менеджер по продажам в стартапе vs. в крупной корпорации).</li>
    <li class="list-group-item">Динамика: ваши интересы и склонности могут меняться со временем — рекомендуется периодически повторять опросник.</li>
    <li class="list-group-item">Ограничения: опросник даёт общую картину. Для глубокой диагностики обратитесь к профориентологу.</li>
</ul>
""",
}

# ============================================================
# Уровни для Big5
# ============================================================
BIG5_DATA = {
    "levels": {
        "low": {
            "title": "Низкий уровень",
            "description": "Черта выражена слабо",
            "color": "secondary",
        },
        "medium": {
            "title": "Средний уровень",
            "description": "Черта выражена умеренно",
            "color": "info",
        },
        "high": {
            "title": "Высокий уровень",
            "description": "Черта выражена сильно",
            "color": "success",
        },
    },
    "important_notes": """
<ul class="list-group list-group-flush">
    <li class="list-group-item">Нет «правильных» или «неправильных» результатов: все черты имеют свои преимущества и сложности.</li>
    <li class="list-group-item">Контекст важен: в разных ситуациях полезны разные черты (например, нейротизм может усиливать эмпатию, а интроверсия — глубину анализа).</li>
    <li class="list-group-item">Результаты — ориентир, а не диагноз: опросник даёт общую картину личности. Для глубокой диагностики обратитесь к психологу.</li>
    <li class="list-group-item">Динамика: черты относительно стабильны, но могут меняться под влиянием опыта, обучения и терапии.</li>
</ul>
""",
}

# ============================================================
# Уровни для Gardner
# ============================================================
GARDNER_DATA = {
    "levels": {
        "low": {
            "title": "Низкий уровень",
            "description": "Тип интеллекта развит слабо",
            "color": "secondary",
        },
        "medium": {
            "title": "Средний уровень",
            "description": "Тип интеллекта развит умеренно",
            "color": "info",
        },
        "high": {
            "title": "Высокий уровень",
            "description": "Тип интеллекта развит хорошо",
            "color": "success",
        },
    },
}

# ============================================================
# Рекомендации по использованию результатов
# ============================================================

# DigCompEdu рекомендации
DIGCOMP_USAGE = {
    "employee": {
        "title": "Рекомендации для респондентов",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Определите 1–2 области с наименьшими баллами — начните с них план развития.</div>
    <div class="list-group-item">Поставьте SMART-цели (например: «Освоить основы фоторедактирования на уровне B1 за 2 месяца»).</div>
    <div class="list-group-item">Используйте результаты для составления резюме или обсуждения карьерного роста.</div>
</div>
""",
    },
    "employer": {
        "title": "Рекомендации для организаций и HR",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Проведите групповую диагностику для выявления общих зон роста сотрудников.</div>
    <div class="list-group-item">Разработайте целевые программы повышения квалификации.</div>
    <div class="list-group-item">Сформируйте «цифровые команды» из сотрудников уровня B2–C1 для поддержки коллег.</div>
</div>
""",
    },
    "university": {
        "title": "Рекомендации для образовательных платформ",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Адаптируйте содержание курсов под реальные потребности аудитории.</div>
    <div class="list-group-item">Предлагайте дифференцированные задания для разных уровней владения компетенциями.</div>
</div>
""",
    },
}

# RIASEC рекомендации
RIASEC_USAGE = {
    "employee": {
        "title": "Рекомендации для самоопределения и карьерного планирования",
        "recommendations": """
<h6 class="mt-2 mb-2">Для самоопределения:</h6>
<div class="list-group list-group-flush mb-3">
    <div class="list-group-item">Используйте карьерный код для поиска профессий, соответствующих вашим склонностям.</div>
    <div class="list-group-item">Обратите внимание на сочетание доминирующих типов — оно даёт более точную картину ваших предпочтений.</div>
    <div class="list-group-item">Рассмотрите смежные области, где пересекаются ваши сильные стороны.</div>
</div>
<h6 class="mt-2 mb-2">Для профориентации и карьерного планирования:</h6>
<div class="list-group list-group-flush">
    <div class="list-group-item">Соотнесите результаты с реальными профессиями через справочники профессий или онлайн-ресурсы.</div>
    <div class="list-group-item">Изучите требования к профессиям, которые вас интересуют, и сравните их с вашими склонностями.</div>
    <div class="list-group-item">Подумайте о дополнительном образовании или курсах, которые помогут развить сильные стороны.</div>
</div>
""",
    },
    "employer": {
        "title": "Рекомендации для работодателей и HR-специалистов",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Используйте опросник для подбора персонала с учётом личностных склонностей.</div>
    <div class="list-group-item">Формируйте команды с учётом разнообразия типов личности для баланса навыков.</div>
    <div class="list-group-item">Подбирайте задачи и проекты, соответствующие доминирующим типам сотрудников.</div>
</div>
""",
    },
    "university": {
        "title": "Рекомендации для образовательных учреждений",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Адаптируйте учебные программы под склонности студентов.</div>
    <div class="list-group-item">Предлагайте элективные курсы, развивающие сильные стороны разных типов личности.</div>
    <div class="list-group-item">Организуйте профориентационные мероприятия с учётом модели RIASEC.</div>
</div>
""",
    },
}

# Big5 рекомендации
BIG5_USAGE = {
    "employee": {
        "title": "Рекомендации для самоанализа и профориентации",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Используйте результаты для понимания своих сильных сторон и зон роста. Высокая добросовестность поможет в карьере, а работа над нейротизмом улучшит стрессоустойчивость.</div>
    <div class="list-group-item">Экстраверты могут преуспеть в продажах и менеджменте, люди с высокой открытостью — в творческих профессиях, добросовестные — в аналитике и инженерии.</div>
</div>
""",
    },
    "employer": {
        "title": "Рекомендации для HR и командной работы",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Учитывайте черты коллег для оптимального распределения ролей (добросовестный сотрудник — для задач с чёткими сроками, открытый — для генерации идей).</div>
    <div class="list-group-item">Используйте результаты для формирования сбалансированных команд.</div>
</div>
""",
    },
    "university": {
        "title": "Рекомендации для образовательных учреждений",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Учитывайте индивидуальные особенности студентов при профориентации.</div>
    <div class="list-group-item">Помогайте студентам развивать сильные стороны и работать над зонами роста.</div>
</div>
""",
    },
}

# Gardner рекомендации
GARDNER_USAGE = {
    "employee": {
        "title": "Рекомендации для саморазвития и карьеры",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Используйте сильные стороны для достижения целей, развивайте слабые через целенаправленные упражнения.</div>
    <div class="list-group-item">В образовании выбирайте форматы обучения, соответствующие доминирующим типам (пространственный — инфографика, телесно-кинестетический — практика).</div>
    <div class="list-group-item">В карьере ориентируйтесь на профессии, где ваши сильные типы интеллекта будут востребованы.</div>
    <div class="list-group-item">В команде учитывайте типы коллег для оптимального распределения ролей.</div>
</div>
""",
    },
    "employer": {
        "title": "Рекомендации для HR",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Учитывайте типы интеллекта при подборе персонала.</div>
    <div class="list-group-item">Формируйте команды с разнообразными типов интеллекта для баланса.</div>
    <div class="list-group-item">Распределяйте задачи с учётом сильных сторон сотрудников.</div>
</div>
""",
    },
    "university": {
        "title": "Рекомендации для образовательных учреждений",
        "recommendations": """
<div class="list-group list-group-flush">
    <div class="list-group-item">Адаптируйте учебные программы под разные типы интеллекта студентов.</div>
    <div class="list-group-item">Предлагайте разнообразные форматы обучения.</div>
    <div class="list-group-item">Помогайте студентам определить свои сильные стороны.</div>
</div>
""",
    },
}


def load_levels(survey_type, data):
    """Загрузка уровней"""
    print(f"Загрузка уровней {survey_type}...")
    for level_code, level_data in data.get("levels", {}).items():
        for user_type in ["employee", "employer", "university", "common"]:
            obj, created = SurveyInterpretation.objects.update_or_create(
                survey_type=survey_type,
                code=level_code,
                user_type=user_type,
                defaults={
                    "title": level_data.get("title", ""),
                    "description": level_data.get("description", ""),
                    "recommendations": level_data.get("recommendations", ""),
                    "color": level_data.get("color", "secondary"),
                    "is_active": True,
                },
            )
    print(f"  Уровни {survey_type} загружены")


def load_common(survey_type, data):
    """Загрузка важных замечаний"""
    if "important_notes" in data:
        print(f"Загрузка важных замечаний {survey_type}...")
        for user_type in ["employee", "employer", "university", "common"]:
            obj, created = SurveyInterpretation.objects.update_or_create(
                survey_type=survey_type,
                code="common",
                user_type=user_type,
                defaults={
                    "title": "Важные замечания",
                    "important_notes": data["important_notes"],
                    "is_active": True,
                },
            )
        print(f"  Важные замечания {survey_type} загружены")


def load_usage(survey_type, usage_data):
    """Загрузка рекомендаций по использованию"""
    print(f"Загрузка рекомендаций {survey_type}...")
    for user_type, data in usage_data.items():
        obj, created = SurveyInterpretation.objects.update_or_create(
            survey_type=survey_type,
            code="usage",
            user_type=user_type,
            defaults={
                "title": data.get("title", "Рекомендации по использованию результатов"),
                "recommendations": data.get("recommendations", ""),
                "is_active": True,
            },
        )
        print(f"  {survey_type} - {user_type}: {'создана' if created else 'обновлена'}")


def main():
    print("\n" + "=" * 60)
    print("Загрузка интерпретаций для опросов")
    print("=" * 60)

    # Загрузка уровней
    load_levels("digcomp", DIGCOMP_DATA)
    load_levels("riasec", RIASEC_DATA)
    load_levels("big5", BIG5_DATA)
    load_levels("gardner", GARDNER_DATA)

    # Загрузка важных замечаний
    print("\n--- Загрузка важных замечаний ---")
    load_common("digcomp", DIGCOMP_DATA)
    load_common("riasec", RIASEC_DATA)
    load_common("big5", BIG5_DATA)
    load_common("gardner", GARDNER_DATA)

    # Загрузка рекомендаций по использованию
    print("\n--- Загрузка рекомендаций ---")
    load_usage("digcomp", DIGCOMP_USAGE)
    load_usage("riasec", RIASEC_USAGE)
    load_usage("big5", BIG5_USAGE)
    load_usage("gardner", GARDNER_USAGE)

    print("\n" + "=" * 60)
    print("Загрузка завершена успешно!")
    print("=" * 60)


if __name__ == "__main__":
    main()
