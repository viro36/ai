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

from apps.surveys.models import SurveyCategory
from django.db import models

# Данные для опросов
SURVEY_DATA = {
    "digcomp": {
        "instruction": """Оцените, насколько утверждения ниже соответствуют вашим навыкам и практике использования цифровых технологий. Используйте шкалу от 1 до 5.""",
        "result_description": """
<h4>Структура DigCompEdu</h4>

<div class="alert alert-info">
    <p>Рамка включает 6 областей компетенций и 22 базовые компетенции.</p>
</div>

<div class="row g-3">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">1. Профессиональное взаимодействие</h5>
            </div>
            <div class="card-body">
                <p>Использование цифровых инструментов для профессионального развития, коммуникации и рефлексии.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">2. Цифровые ресурсы</h5>
            </div>
            <div class="card-body">
                <p>Поиск, создание и распространение цифрового контента.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">3. Преподавание и обучение</h5>
            </div>
            <div class="card-body">
                <p>Интеграция цифровых технологий в образовательный процесс.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">4. Оценка</h5>
            </div>
            <div class="card-body">
                <p>Использование цифровых инструментов для оценивания и обратной связи.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">5. Расширение возможностей учащихся</h5>
            </div>
            <div class="card-body">
                <p>Применение цифровых технологий для персонализации обучения.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">6. Формирование цифровой компетентности учащихся</h5>
            </div>
            <div class="card-body">
                <p>Помощь ученикам в развитии цифровых навыков.</p>
            </div>
        </div>
    </div>
</div>

<h5 class="mt-4">Уровни владения компетенциями DigCompEdu</h5>

<div class="table-responsive">
    <table class="table table-bordered">
        <thead class="table-light">
            <tr>
                <th>Уровень</th>
                <th>Описание</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>A1 (новичок)</td><td>Осведомлённость о потенциале технологий, использование небольшого количества цифровых инструментов.</td></tr>
            <tr><td>A2 (исследователь)</td><td>Заинтересованность в изучении цифровых технологий, но использование непоследовательное.</td></tr>
            <tr><td>B1 (интегратор)</td><td>Применение цифровых технологий в различных контекстах.</td></tr>
            <tr><td>B2 (эксперт)</td><td>Профессиональное, творческое и критическое использование цифровых инструментов.</td></tr>
            <tr><td>C1 (лидер)</td><td>Обладание гибким и эффективным набором цифровых стратегий.</td></tr>
            <tr><td>C2 (новатор)</td><td>Критическое переосмысление стандартных практик, разработка передовых методик.</td></tr>
        </tbody>
    </table>
</div>
""",
    },
    "riasec": {
        "instruction": """Перед вами список занятий и профессий. Оцените каждое утверждение по шкале от 1 до 5, насколько вам нравится или подходит это занятие/профессия.""",
        "result_description": """
<h4>6 типов личности по Холланду (RIASEC)</h4>

<div class="accordion" id="riasecAccordion">
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseR">
                Реалистичный (R - Realistic)
            </button>
        </h2>
        <div id="collapseR" class="accordion-collapse collapse show" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> техника, инструменты, физические действия, работа с объектами.</p>
                <p><strong>Черты:</strong> практичность, целеустремлённость, ориентация на настоящее, эмоциональная стабильность.</p>
                <p><strong>Примеры профессий:</strong> инженер, механик, электрик, фермер, строитель, пилот.</p>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseI">
                Исследовательский (I - Investigative)
            </button>
        </h2>
        <div id="collapseI" class="accordion-collapse collapse" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> анализ информации, решение абстрактных задач, научные исследования.</p>
                <p><strong>Черты:</strong> любознательность, аналитичность, методичность, независимость.</p>
                <p><strong>Примеры профессий:</strong> учёный, исследователь, аналитик данных, биолог, физик.</p>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseA">
                Артистический (A - Artistic)
            </button>
        </h2>
        <div id="collapseA" class="accordion-collapse collapse" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> творчество, самовыражение, искусство, нестандартные решения.</p>
                <p><strong>Черты:</strong> креативность, эмоциональность, интуитивность, независимость.</p>
                <p><strong>Примеры профессий:</strong> художник, музыкант, актёр, писатель, дизайнер, архитектор.</p>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseS">
                Социальный (S - Social)
            </button>
        </h2>
        <div id="collapseS" class="accordion-collapse collapse" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> помощь людям, обучение, консультирование, развитие других.</p>
                <p><strong>Черты:</strong> эмпатия, коммуникабельность, гуманность, активность.</p>
                <p><strong>Примеры профессий:</strong> учитель, психолог, врач, социальный работник, тренер.</p>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseE">
                Предпринимательский (E - Enterprising)
            </button>
        </h2>
        <div id="collapseE" class="accordion-collapse collapse" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> управление, убеждение, бизнес, достижение целей, риск.</p>
                <p><strong>Черты:</strong> амбициозность, энергичность, лидерские качества, ориентация на результат.</p>
                <p><strong>Примеры профессий:</strong> менеджер, предприниматель, маркетолог, политик, PR-специалист.</p>
            </div>
        </div>
    </div>
    <div class="accordion-item">
        <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseC">
                Конвенциональный (C - Conventional)
            </button>
        </h2>
        <div id="collapseC" class="accordion-collapse collapse" data-bs-parent="#riasecAccordion">
            <div class="accordion-body">
                <p><strong>Интересы:</strong> организация, порядок, работа с данными, структурированные задачи.</p>
                <p><strong>Черты:</strong> организованность, аккуратность, практичность, следование правилам.</p>
                <p><strong>Примеры профессий:</strong> бухгалтер, экономист, администратор, секретарь.</p>
            </div>
        </div>
    </div>
</div>
""",
    },
    "big5": {
        "instruction": """Перед вами список утверждений о поведении и чувствах. Прочитайте каждое утверждение и выберите вариант ответа, который наиболее точно отражает ваше мнение. Отвечайте, опираясь на то, как вы обычно себя ведёте и что чувствуете, а не на то, как хотели бы себя вести.""",
        "result_description": """
<h4>5 факторов модели Big Five</h4>

<div class="row g-3">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">Экстраверсия (Extraversion)</h5>
            </div>
            <div class="card-body">
                <p><strong>Высокие показатели:</strong> общительность, энергичность, инициативность, оптимизм.</p>
                <p><strong>Низкие показатели:</strong> сдержанность, потребность в уединении, предпочтение небольших групп.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">Доброжелательность (Agreeableness)</h5>
            </div>
            <div class="card-body">
                <p><strong>Высокие:</strong> дружелюбие, эмпатия, готовность к сотрудничеству, доверчивость.</p>
                <p><strong>Низкие:</strong> скептицизм, соревновательность, склонность к конфликтам.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">Добросовестность (Conscientiousness)</h5>
            </div>
            <div class="card-body">
                <p><strong>Высокие:</strong> организованность, самодисциплина, ответственность, аккуратность.</p>
                <p><strong>Низкие:</strong> спонтанность, хаотичность, низкая саморегуляция.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">Нейротизм / Эмоциональная стабильность</h5>
            </div>
            <div class="card-body">
                <p><strong>Высокие:</strong> тревожность, эмоциональная неустойчивость, склонность к стрессу.</p>
                <p><strong>Низкие:</strong> спокойствие, стрессоустойчивость, ровное настроение.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-header text-white">
                <h5 class="card-title mb-0">Открытость опыту (Openness to Experience)</h5>
            </div>
            <div class="card-body">
                <p><strong>Высокие:</strong> любознательность, креативность, гибкость мышления, любовь к новизне.</p>
                <p><strong>Низкие:</strong> консервативность, предпочтение привычного, практичность.</p>
            </div>
        </div>
    </div>
</div>
""",
    },
    "gardner": {
        "instruction": """Перед вами список утверждений о ваших предпочтениях, способностях и поведении. Прочитайте каждое утверждение и выберите вариант ответа, который наиболее точно отражает вашу реальность. Отвечайте искренне — нет «правильных» или «неправильных» ответов.""",
        "result_description": """
<h4>8 (9) типов интеллекта по Гарднеру</h4>

<div class="row g-3">
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Лингвистический</h5>
                <p class="card-text">Способность эффективно использовать слова (устно и письменно), любовь к чтению, письму, языковым играм.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Логико-математический</h5>
                <p class="card-text">Логическое мышление, работа с числами, закономерностями, абстрактными понятиями.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Пространственный</h5>
                <p class="card-text">Умение визуализировать, ориентироваться в пространстве, работать с образами и схемами.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Музыкальный</h5>
                <p class="card-text">Восприятие и создание музыки, чувство ритма, мелодии, гармонии.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Телесно-кинестетический</h5>
                <p class="card-text">Координация, ловкость, владение телом, практические навыки, спорт, ремесло.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Межличностный</h5>
                <p class="card-text">Понимание других людей, эмпатия, коммуникация, лидерство, работа в команде.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Внутриличностный</h5>
                <p class="card-text">Самопознание, саморефлексия, понимание собственных эмоций и мотивов.</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">Натуралистический</h5>
                <p class="card-text">Интерес к природе, классификация живых существ, наблюдение за экосистемами.</p>
            </div>
        </div>
    </div>
</div>

<div class="alert alert-secondary mt-3">
    <strong>Опционально:</strong> Экзистенциальный (философский) — склонность к размышлениям о смысле жизни, глобальных вопросах бытия.
</div>
""",
    },
}


def add_survey_descriptions():
    """Добавление инструкций и описаний результатов для опросов"""

    print("\n" + "=" * 60)
    print("Добавление инструкций и описаний результатов")
    print("=" * 60 + "\n")

    for survey_key, data in SURVEY_DATA.items():
        # Ищем категорию по названию (с учётом разных вариантов)
        if survey_key == "big5":
            categories = SurveyCategory.objects.filter(
                models.Q(name__icontains="Большая пятёрка")
                | models.Q(name__icontains="Big 5")
                | models.Q(name__icontains="Big5")
            )
        elif survey_key == "gardner":
            categories = SurveyCategory.objects.filter(
                models.Q(name__icontains="Гарднер")
                | models.Q(name__icontains="Gardner")
                | models.Q(name__icontains="модели Говарда Гарднера")
            )
        else:
            categories = SurveyCategory.objects.filter(name__icontains=survey_key)

        if not categories.exists():
            print(f"Опрос '{survey_key}' не найден в базе данных. Пропускаем.")
            continue

        for category in categories:
            updated = False

            if "instruction" in data:
                category.instruction_text = data["instruction"]
                updated = True

            if "result_description" in data:
                category.result_description = data["result_description"]
                updated = True

            if updated:
                category.save()
                print(f"Обновлён опрос: {category.name}")
            else:
                print(f"Нет данных для обновления: {category.name}")

    print("\n" + "=" * 60)
    print("Инструкции и описания результатов добавлены!")
    print("=" * 60)


if __name__ == "__main__":
    add_survey_descriptions()
