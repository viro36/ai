import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser
from django.db import transaction
from apps.courses.models import Course

logger = logging.getLogger(__name__)


class VstuParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3662020886",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ"',
            short_name="ВГТУ",
            address_raw="г. Воронеж, Московский проспект, 14",
        )
        self.BASE_URL = "https://dpo.cchgeu.ru"

        self.AI_KEYWORDS = [
            "искусственный интеллект",
            "нейросети",
            "машинное обучение",
            "ai",
            "робототехника",
            "беспилотный",
            "беспилотная",
            "программируемых систем",
        ]

    def get_courses_list(self):
        """Сбор ссылок на ИИ-курсы со страницы списка"""
        courses_data = []

        sections = [
            "/professionalnaya-perepodgotovka/",
            "/kursy-povysheniya-kvalifikatsii/",
            "/kursy-dlya-pedagogicheskikh-rabotnikov/",
        ]

        for section in sections:
            page_num = 1
            while True:
                url = f"{self.BASE_URL}{section}"
                if page_num > 1:
                    url = f"{self.BASE_URL}{section}?PAGEN_1={page_num}"

                try:
                    logger.info(f"Загрузка страницы {page_num}: {url}")
                    response = self.session.get(url, headers=self.HEADERS, timeout=30)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Ошибка при загрузке {url}: {e}")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select(".kurs-card")

                if not cards:
                    break

                for card in cards:
                    name_link = card.select_one(".kurs-name")
                    if not name_link:
                        continue

                    title = name_link.get_text(strip=True)
                    link = name_link.get("href")

                    direction_p = card.find("p")
                    direction = (
                        direction_p.get_text(strip=True)
                        .replace("Направление:", "")
                        .strip()
                        if direction_p
                        else ""
                    )

                    if not self._is_ai_related(f"{title} {direction}"):
                        continue

                    full_url = self.BASE_URL + link if link.startswith("/") else link

                    courses_data.append(
                        {
                            "url": full_url,
                            "title": title,
                            "category_text": direction,
                        }
                    )
                    logger.info(f"ИИ-курс найден: {title}")

                next_link = soup.select_one(".bx-pag-next a")
                if next_link and "href" in next_link.attrs:
                    page_num += 1
                else:
                    break

        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса с помощью регулярных выражений"""
        course_url = course_info.get("url")

        if not course_url:
            logger.error("Пустой URL курса")
            return None, False

        try:
            logger.info(f"Загрузка детальной страницы: {course_url}")
            response = self.session.get(course_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка загрузки {course_url}: {e}")
            return None, False

        soup = BeautifulSoup(response.text, "html.parser")

        # Название
        title = course_info.get("title", "")
        h1_title = soup.select_one(".middle h1")
        if h1_title:
            title = h1_title.get_text(strip=True)

        # Получаем весь текст страницы
        page_text = soup.get_text()

        # Извлекаем данные через регулярные выражения
        # Продолжительность (часы)
        duration_hours = None
        duration_match = re.search(r"Продолжительность:\s*(\d+)\s*часа", page_text)
        if duration_match:
            duration_hours = int(duration_match.group(1))

        # Форма обучения
        format_text = ""
        format_match = re.search(r"Форма обучения:\s*([^\n]+?)(?:\n|$)", page_text)
        if format_match:
            format_text = format_match.group(1).strip()

        # Стоимость
        price = ""
        price_match = re.search(r"Стоимость:\s*(\d+)\s*руб", page_text)
        if price_match:
            price = f"{price_match.group(1)} руб."

        # Выдаваемый документ
        document_type = ""
        doc_match = re.search(r"Выдаваемый документ:\s*([^\n]+)", page_text)
        if doc_match:
            document_type = doc_match.group(1).strip()

        # Описание (после "Описание:" до следующего заголовка)
        description = ""
        desc_match = re.search(
            r"Описание:\s*\n?\s*(.*?)(?=\n\s*\n\s*Ключевые особенности|\n\s*\n\s*Категория слушателей|\n\s*\n\s*Требования|\Z)",
            page_text,
            re.DOTALL,
        )
        if desc_match:
            description = desc_match.group(1).strip()
            # Очищаем от лишних пробелов
            description = re.sub(r"\n+", "\n", description)
            description = description[:5000]

        # Темы
        topics = ""
        topics_match = re.search(
            r"Темы:\s*\n?\s*(.*?)(?=\n\s*\n\s*Итоговая|\Z)", page_text, re.DOTALL
        )
        if topics_match:
            topics = topics_match.group(1).strip()
            topics = re.sub(r"\n+", "\n", topics)
            topics = topics[:10000]

        # Преподаватели
        teachers = ""
        teacher_match = re.search(
            r"([А-Я][а-я]+\s+[А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)\s*\n\s*(?:Доцент|Профессор)",
            page_text,
        )
        if teacher_match:
            teachers = teacher_match.group(1).strip()

        print(f"  Название: {title}")
        print(f"  Длительность (часы): {duration_hours}")
        print(f"  Форма: {format_text}")
        print(f"  Стоимость: {price}")
        print(f"  Документ: {document_type}")
        print(f"  Преподаватели: {teachers}")

        with transaction.atomic():
            course, created = Course.objects.update_or_create(
                url=course_url,
                defaults={
                    "title": title,
                    "description": description[:5000],
                    "duration_hours": duration_hours,
                    "format": format_text[:100],
                    "price": price[:100],
                    "teachers": teachers[:500],
                    "topics": topics[:10000],
                    "organization": self.organization,
                    "field_of_study": course_info.get("category_text", ""),
                },
            )
            if course_info.get("category_text"):
                self._assign_categories(course, course_info.get("category_text", ""))

        return course, created
