from django.core.management.base import BaseCommand
from apps.technical_requirements.models import Question


class Command(BaseCommand):
    help = "Создает начальные вопросы для формы технического задания"

    def handle(self, *args, **options):
        questions_data = [
            {
                "order": 1,
                "text": "Проблема (для решения какой конкретной проблемы или в связи с какими вновь возникшими обстоятельствами необходимо обучение сотрудников?)",
                "question_type": "textarea",
                "is_required": True,
                "placeholder": "Опишите проблему...",
            },
            {
                "order": 2,
                "text": "Цель обучения (что должны уметь сотрудники в итоге?)",
                "question_type": "textarea",
                "is_required": True,
                "placeholder": "Опишите цели...",
            },
            {
                "order": 3,
                "text": "Ключевые слова, характеризующие желаемое содержание программы",
                "question_type": "choice",
                "is_required": True,
                "options": [
                    "Автоматизация",
                    "Внедрение ИИ",
                    "Бережливое управление",
                    "Снижение затрат",
                    "Повышение производительности труда",
                    "Передовые практики в отрасли",
                    "Свой вариант",
                ],
            },
            {
                "order": 4,
                "text": "Необходимо ли обучение на конкретном оборудовании?",
                "question_type": "boolean",
                "is_required": True,
            },
            {
                "order": 5,
                "text": "Точное наименование оборудования (марка, модель, год выпуска и т.д.)",
                "question_type": "textarea",
                "is_required": False,
                "depends_on_id": 4,
                "depends_value": "True",
                "placeholder": "Укажите оборудование...",
            },
            {
                "order": 6,
                "text": "Возможна ли организация практики непосредственно на производственной площадке заказчика программы?",
                "question_type": "boolean",
                "is_required": False,
                "depends_on_id": 4,
                "depends_value": "True",
            },
            {
                "order": 7,
                "text": "Необходима ли выездная стажировка?",
                "question_type": "boolean",
                "is_required": True,
            },
            {
                "order": 8,
                "text": "Желаемая площадка стажировки",
                "question_type": "text",
                "is_required": False,
                "depends_on_id": 7,
                "depends_value": "True",
                "placeholder": "Название организации или площадки",
            },
            {
                "order": 9,
                "text": "Возможно ли проведение внешнего аудита представителями образовательной организации для более детальной проработки предложения?",
                "question_type": "boolean",
                "is_required": True,
            },
            {
                "order": 10,
                "text": "Целевая аудитория (кто будет проходить обучение? Указываются статусно-ролевые позиции)",
                "question_type": "textarea",
                "is_required": True,
                "placeholder": "Например: руководители среднего звена, IT-специалисты...",
            },
            {
                "order": 11,
                "text": "Сколько человек всего планируете обучить по запрашиваемой программе?",
                "question_type": "number",
                "is_required": True,
                "placeholder": "Введите количество",
            },
            {
                "order": 12,
                "text": "Желаемая форма организации обучения",
                "question_type": "choice",
                "is_required": True,
                "options": [
                    "Полностью дистанционно",
                    "Частично дистанционно",
                    "Очно без отрыва от производства",
                    "Очно с отрывом от производства",
                ],
            },
            {
                "order": 13,
                "text": "Желаемая дата начала программы",
                "question_type": "date",
                "is_required": True,
            },
            {
                "order": 14,
                "text": "Желаемая дата окончания программы",
                "question_type": "date",
                "is_required": True,
            },
            {
                "order": 15,
                "text": "Желаемая длительность программы обучения",
                "question_type": "choice",
                "is_required": True,
                "options": ["12 часов", "24 часа", "72 часа", "144 часа", "256 часов"],
            },
            {
                "order": 16,
                "text": "Желаемая стоимость обучения одного сотрудника, руб.",
                "question_type": "number",
                "is_required": True,
                "placeholder": "Введите сумму в рублях",
            },
            {
                "order": 17,
                "text": "Желаемая форма реализации программы",
                "question_type": "choice",
                "is_required": True,
                "options": [
                    "Сетевая организация (группы из сотрудников разных предприятий, снижение стоимости обучения одного человека)",
                    "Корпоративная программа (обучение сотрудников только одного предприятия)",
                ],
            },
            {
                "order": 18,
                "text": "Контактное лицо для консультирования в процессе разработки программы (ФИО, должность, телефон)",
                "question_type": "textarea",
                "is_required": True,
                "placeholder": "Иванов Иван Иванович, директор, +7 999 123-45-67",
                "help_text": "ВНИМАНИЕ: предложение программ поступят в ваш личный кабинет на платформе. Не принимайте и не рассматривайте их иным способом",
            },
        ]

        for data in questions_data:
            depends_on_id = data.pop("depends_on_id", None)
            question, created = Question.objects.get_or_create(
                order=data["order"], defaults=data
            )
            if depends_on_id:
                try:
                    depends_on = Question.objects.get(order=depends_on_id)
                    question.depends_on = depends_on
                    question.save()
                except Question.DoesNotExist:
                    pass

            if created:
                self.stdout.write(
                    f'Создан вопрос #{data["order"]}: {data["text"][:50]}...'
                )
            else:
                self.stdout.write(f'Вопрос #{data["order"]} уже существует')

        self.stdout.write(self.style.SUCCESS("Начальные вопросы успешно созданы!"))
