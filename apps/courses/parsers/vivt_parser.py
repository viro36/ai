import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser
from apps.courses.models import Category

logger = logging.getLogger(__name__)


class VivtParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3662006761",
            full_name='АНОО ВО "ВОРОНЕЖСКИЙ ИНСТИТУТ ВЫСОКИХ ТЕХНОЛОГИЙ"',
            short_name="ВИВТ",
            address_raw="г. Воронеж, ул. Ленина, 73а",
        )
        self.BASE_URL = "https://vivt.ru"
        self.program_pages = [
            {"url": "/dpo/program/it", "category": "Информационные технологии"},
            {
                "url": "/dpo/program/electronnaya-torgovlya",
                "category": "Государственные и муниципальные закупки",
            },
            {
                "url": "/dpo/program/programmy-obucheniya-rabotnikov-sfery-obrazovaniya",
                "category": "Программы для работников образования",
            },
            {
                "url": "/dpo/program/business-school",
                "category": "Бизнес школа менеджеров",
            },
        ]

    def _get_or_create_category(self, category_name):
        """Создаёт или находит категорию"""
        if not category_name:
            return None
        category, created = Category.objects.get_or_create(name=category_name)
        if created:
            logger.info(f"Создана категория: {category_name}")
        return category

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со всех страниц программ"""
        courses_data = []

        for page_info in self.program_pages:
            page_url = page_info["url"]
            category_name = page_info["category"]
            full_url = self.BASE_URL + page_url

            category = self._get_or_create_category(category_name)
            if not category:
                logger.warning(f"Категория не найдена для {page_url}")
                continue

            try:
                logger.info(
                    f"Загрузка страницы: {full_url} (категория: {category_name})"
                )
                response = self.session.get(full_url, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Ошибка при загрузке {full_url}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(".program-card")

            for card in cards:
                program_type_code = card.get("data-typeprogram")
                if program_type_code == "4":
                    program_type = "Профессиональная переподготовка"
                elif program_type_code == "3":
                    program_type = "Повышение квалификации"
                else:
                    program_type = ""

                title_elem = card.select_one(".program-card__title h4")
                title = title_elem.get_text(strip=True) if title_elem else ""

                price = ""
                price_elem = card.select_one(".program-card__price b")
                if price_elem:
                    price = price_elem.get_text(strip=True)

                format_text = ""
                format_elem = card.select_one(".program-card__education b")
                if format_elem:
                    format_text = format_elem.get_text(strip=True)

                duration_hours = None
                duration_elem = card.select_one(".program-card__duration b")
                if duration_elem:
                    duration_text = duration_elem.get_text(strip=True)
                    hours_match = re.search(r"(\d+)\s*(?:часа|часов|ч)", duration_text)
                    if hours_match:
                        duration_hours = int(hours_match.group(1))

                start_dates = ""
                start_elem = card.select_one(".program-card__beginning b")
                if start_elem:
                    start_dates = start_elem.get_text(strip=True)

                subtitle_elem = card.select_one(".program-card__subtitle")
                description = ""
                target_audience = ""
                topics = ""

                if subtitle_elem:
                    full_text = subtitle_elem.get_text(strip=True)

                    audience_match = re.search(
                        r"Для кого курс[:\s]+(.+?)(?=В программе курса|$)",
                        full_text,
                        re.IGNORECASE | re.DOTALL,
                    )
                    if audience_match:
                        target_audience = audience_match.group(1).strip()

                    topics_match = re.search(
                        r"В программе курса[:\s]+(.+?)(?=Набор в группу|Старт программы|$)",
                        full_text,
                        re.IGNORECASE | re.DOTALL,
                    )
                    if topics_match:
                        topics = topics_match.group(1).strip()

                    desc_match = re.search(
                        r"^(.*?)(?=Для кого курс)", full_text, re.IGNORECASE | re.DOTALL
                    )
                    if desc_match:
                        description = desc_match.group(1).strip()

                # Уникальный URL из ID курса
                course_id = card.get("id")
                if course_id:
                    unique_url = f"{self.BASE_URL}/dpo/program?course={course_id}"
                else:
                    slug = re.sub(r"[^a-zA-Zа-яА-Я0-9\s-]", "", title)
                    slug = re.sub(r"[-\s]+", "-", slug).strip("-").lower()
                    if len(slug) > 50:
                        slug = slug[:50]
                    unique_url = f"{full_url}?course={slug}"

                courses_data.append(
                    {
                        "url": unique_url,
                        "title": title,
                        "program_type": program_type,
                        "duration_hours": duration_hours,
                        "format_text": format_text,
                        "price": price,
                        "start_dates": start_dates,
                        "target_audience": target_audience,
                        "topics": topics,
                        "description": description,
                        "category": category,
                    }
                )

                logger.info(f"Найден курс: {title} ({program_type}) - {category_name}")

        logger.info(f"Всего найдено курсов ВИВТ: {len(courses_data)}")
        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса"""
        course_url = course_info.get("url")

        if not course_url:
            logger.error("Пустой URL")
            return None, False

        title = course_info.get("title", "")
        program_type = course_info.get("program_type", "")
        duration_hours = course_info.get("duration_hours")
        format_text = course_info.get("format_text", "")
        price = course_info.get("price", "")
        start_dates = course_info.get("start_dates", "")
        target_audience = course_info.get("target_audience", "")
        topics = course_info.get("topics", "")
        description = course_info.get("description", "")
        category = course_info.get("category")

        logger.info(f"  Название: {title}")
        logger.info(f"  Тип программы: {program_type}")
        logger.info(f"  Длительность (часы): {duration_hours}")
        logger.info(f"  Форма обучения: {format_text}")
        logger.info(f"  Стоимость: {price}")
        logger.info(f"  Период набора: {start_dates}")

        defaults = {
            "title": title[:500] if title else "",
            "program_type": program_type[:200] if program_type else "",
            "duration_hours": duration_hours,
            "format": format_text[:100] if format_text else "",
            "price": price[:100] if price else "",
            "start_dates": start_dates[:200] if start_dates else "",
            "target_audience": target_audience[:2000] if target_audience else "",
            "topics": topics[:10000] if topics else "",
            "description": description[:5000] if description else "",
            "study_mode": "Очно-заочная",
        }

        # Сохраняем курс
        course, created = self._update_course(course_url, defaults)

        # Добавляем категорию (НЕ удаляем существующие!)
        if course and category:
            # Проверяем, есть ли уже такая категория у курса
            if not course.categories.filter(id=category.id).exists():
                course.categories.add(category)
                logger.info(f"  Добавлена категория: {category.name}")
            else:
                logger.info(f"  Категория уже есть: {category.name}")

        return course, created
