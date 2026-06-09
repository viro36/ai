import requests
import logging
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from apps.organizations.models import Organization
from apps.courses.models import Category

logger = logging.getLogger(__name__)


class BaseParser:
    """Базовый класс для всех парсеров курсов"""

    BASE_URL = ""
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }
    AI_KEYWORDS = [
        "ии",
        "ии-грамотность",
        "искусственный интеллект",
        "нейросети",
        "машинное обучение",
        "ai",
        "нейронные сети",
        "глубокое обучение",
        "data science",
        "анализ данных",
    ]

    def __init__(self, inn, full_name, short_name, address_raw=""):
        # Настройка сессии с повторными попытками
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Поиск или создание организации в БД
        try:
            self.organization = Organization.objects.get(inn=inn)
        except Organization.DoesNotExist:
            self.organization = Organization.objects.create(
                inn=inn,
                full_name=full_name,
                short_name=short_name,
                address_raw=address_raw,
            )

    def _is_ai_related(self, text):
        """Проверка, относится ли текст к ИИ"""
        text = text.lower()
        for keyword in self.AI_KEYWORDS:
            if " " in keyword:
                if keyword in text:
                    return True
            else:
                if re.search(rf"\b{re.escape(keyword)}\b", text):
                    return True
        return False

    def _assign_categories(self, course, category_text):
        """Привязка категорий к курсу"""
        if not category_text or not category_text.strip():
            return

        cat_names = [c.strip() for c in category_text.split(",") if c.strip()]
        for name in cat_names:
            if not name or not any(c.isalpha() for c in name):
                continue

            try:
                cat = Category.objects.filter(name=name).first()
                if not cat:
                    from django.utils.text import slugify

                    slug = slugify(name)
                    if not slug:
                        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                    if Category.objects.filter(slug=slug).exists():
                        import random

                        slug = f"{slug}-{random.randint(1000, 9999)}"
                    cat = Category(name=name, slug=slug)
                    cat.save()
                    print(f"Создана категория: {name} (slug: {slug})")
                else:
                    print(f"Категория уже существует: {name} (slug: {cat.slug})")
                course.categories.add(cat)
            except Exception as e:
                print(f"Ошибка с категорией '{name}': {e}")

    def get_courses_list(self):
        """Получить список курсов (должен быть переопределён в дочернем классе)"""
        raise NotImplementedError("Метод get_courses_list должен быть переопределён")

    def parse_course_detail(self, course_url):
        """Парсинг детальной страницы курса (должен быть переопределён)"""
        raise NotImplementedError("Метод parse_course_detail должен быть переопределён")

    def run(self):
        """Основной метод запуска парсера"""
        courses_data = self.get_courses_list()
        print(f"\nНайдено курсов: {len(courses_data)}")

        count_created = 0
        count_updated = 0

        for course_info in courses_data:
            print(f"\nОбработка: {course_info.get('url', '')}")
            course, created = self.parse_course_detail(course_info)
            if course:
                if created:
                    count_created += 1
                    print(f"Создан курс: {course.title}")
                else:
                    count_updated += 1
                    print(f"Обновлён курс: {course.title}")
            time.sleep(0.5)

        logger.info(
            f"Парсинг завершён: создано {count_created}, обновлено {count_updated}"
        )
        return count_created, count_updated
