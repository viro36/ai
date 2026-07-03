from django.core.management.base import BaseCommand
from apps.goal_setting.models import Question, QuestionOption


class Command(BaseCommand):
    help = "Создает начальные вопросы для целеполагания"

    def handle(self, *args, **options):
        # Сначала удаляем старые вопросы
        Question.objects.all().delete()
        self.stdout.write("Старые вопросы удалены")

        questions_data = [
            {
                "order": 1,
                "text": "В связи с чем Вам сейчас необходимо обучение?",
                "description": "Выберите основную причину, которая побудила вас искать образовательную программу",
                "question_type": "choice",
                "is_required": True,
                "is_multiple": False,
                "has_custom_option": True,
                "custom_option_label": "Свой вариант",
                "options": [
                    {"value": "change_profession", "label": "Хочу сменить профессию"},
                    {
                        "value": "improve_qualification",
                        "label": "Хочу повысить квалификацию",
                    },
                    {"value": "career_growth", "label": "Хочу карьерного роста"},
                    {"value": "pass_exam", "label": "Хочу сдать экзамен"},
                    {
                        "value": "production_necessity",
                        "label": "В связи с производственной необходимостью (модернизация, автоматизация, внедрение новых технологий и т.д.)",
                    },
                    {
                        "value": "develop_soft_skills",
                        "label": "Хочу развить надпрофессиональные компетенции",
                    },
                ],
            },
            {
                "order": 2,
                "text": "В чём именно состоит желаемый результат вашего обучения — что должно появиться или измениться по его завершении?",
                "description": "Опишите конкретные навыки, знания или умения, которые вы хотите получить. Начните ответ со слов «я смогу…»",
                "question_type": "text",
                "is_required": True,
                "max_length": 1000,
            },
            {
                "order": 3,
                "text": "Если необходимо освоить в процессе обучения какое-то конкретное программное обеспечение, технологию, оборудование и т.д., то укажите его точное наименование или кратко опишите его функционал",
                "description": "Укажите конкретные инструменты, технологии или оборудование, которые вам нужно изучить (например: 1С:Предприятие, AutoCAD, Python, оборудование ЧПУ, CRM-системы и т.д.)",
                "question_type": "text",
                "is_required": True,
                "max_length": 1000,
            },
            {
                "order": 4,
                "text": "Напишите несколько ключевых слов, отражающих желаемое содержание Вашей программы обучения",
                "description": "Укажите ключевые темы и направления, которые вы хотели бы изучить (например: управление проектами, аналитика данных, цифровой маркетинг, лидерство, бережливое производство, нейросети, разработка ПО)",
                "question_type": "text",
                "is_required": True,
                "max_length": 500,
            },
            {
                "order": 5,
                "text": "Желаемая форма организации обучения",
                "description": "Выберите удобные для вас форматы обучения (можно выбрать несколько)",
                "question_type": "multiple_choice",
                "is_required": True,
                "is_multiple": True,
                "has_custom_option": False,
                "options": [
                    {
                        "value": "fully_online",
                        "label": "Полностью дистанционно (онлайн)",
                    },
                    {
                        "value": "partially_online",
                        "label": "Частично дистанционно (смешанный формат)",
                    },
                    {
                        "value": "offline_without_break",
                        "label": "Очно без отрыва от производства (вечером или в выходные)",
                    },
                    {
                        "value": "offline_with_break",
                        "label": "Очно с отрывом от производства (интенсивные модули)",
                    },
                ],
            },
            {
                "order": 6,
                "text": "Желаемый период обучения",
                "description": "Укажите удобные для вас даты начала и окончания обучения",
                "question_type": "date_range",
                "is_required": True,
            },
        ]

        for q_data in questions_data:
            question, created = Question.objects.get_or_create(
                order=q_data["order"],
                defaults={
                    "text": q_data["text"],
                    "description": q_data.get("description", ""),
                    "question_type": q_data["question_type"],
                    "is_required": q_data["is_required"],
                    "max_length": q_data.get("max_length", 500),
                    "is_active": True,
                    "is_multiple": q_data.get("is_multiple", False),
                    "has_custom_option": q_data.get("has_custom_option", False),
                    "custom_option_label": q_data.get(
                        "custom_option_label", "Свой вариант"
                    ),
                },
            )

            if created:
                self.stdout.write(f"Создан вопрос: {question.text[:50]}...")
            else:
                self.stdout.write(f"Вопрос уже существует: {question.text[:50]}...")

            # Создаём варианты ответов
            if "options" in q_data:
                for i, opt_data in enumerate(q_data["options"]):
                    opt, created = QuestionOption.objects.get_or_create(
                        question=question,
                        value=opt_data["value"],
                        defaults={
                            "label": opt_data["label"],
                            "is_custom": False,
                            "order": i,
                        },
                    )
                self.stdout.write(f"  Создано {len(q_data['options'])} вариантов")

            # Добавляем "Свой вариант" если нужно
            if q_data.get("has_custom_option", False):
                opt, created = QuestionOption.objects.get_or_create(
                    question=question,
                    value="custom",
                    defaults={
                        "label": q_data.get("custom_option_label", "Свой вариант"),
                        "is_custom": True,
                        "order": len(q_data.get("options", [])) + 1,
                    },
                )
                if created:
                    self.stdout.write(f"  Создан вариант 'Свой вариант'")

        self.stdout.write(self.style.SUCCESS("\nВсе вопросы успешно созданы!"))
