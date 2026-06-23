import logging
import time
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VsuetParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666026776",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ ИНЖЕНЕРНЫХ ТЕХНОЛОГИЙ"',
            short_name="ВГУИТ",
            address_raw="г. Воронеж, пр-т Революции, 19",
        )
        self.BASE_URL = "https://vsuet.ru"

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страницы списка"""
        courses_data = []
        page_url = "/science/urnt/ido/courses"
        page_num = 1

        while page_url:
            full_url = (
                self.BASE_URL + page_url if page_url.startswith("/") else page_url
            )
            try:
                logger.info(f"Загрузка страницы {page_num}: {full_url}")
                response = self.session.get(full_url, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Ошибка при загрузке {full_url}: {e}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(".article-item")

            for card in cards:
                title_elem = card.select_one(".flip-box__header")
                title = title_elem.get_text(strip=True) if title_elem else ""
                cat_elem = card.select_one(".flip-box__desc")
                category_text = cat_elem.get_text(strip=True) if cat_elem else ""

                btn = card.select_one(".button._bordered")
                if btn and btn.get("href"):
                    url = self.BASE_URL + btn.get("href")
                    courses_data.append(
                        {"url": url, "title": title, "category_text": category_text}
                    )
                    logger.info(f"Найден курс: {title}")

            # Пагинация
            next_link = None
            for item in soup.select(".pagination .page-item"):
                link = item.find("a")
                if link and (
                    link.find("i", class_="fa-angle-right")
                    or "Вперёд" in link.get_text()
                ):
                    next_link = link.get("href")
                    break

            page_url = next_link
            page_num += 1
            time.sleep(1)

        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса"""
        course_url = course_info["url"]
        try:
            response = self.session.get(course_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка загрузки {course_url}: {e}")
            return None, False

        soup = BeautifulSoup(response.text, "html.parser")

        # Название курса
        title = soup.select_one("h2.text-uppercase")
        title = title.get_text(strip=True) if title else course_info["title"]

        # Тип программы
        program_type = soup.select_one("div.text-danger-dark h5")
        program_type = program_type.get_text(strip=True) if program_type else ""

        # Описание
        description = soup.select_one("#courseAbout .fs-18")
        description = description.get_text(strip=True) if description else ""

        # Данные из блока card-panel__info
        format_text = ""
        study_mode = ""
        teachers = ""
        start_dates = ""
        duration_weeks = ""

        for li in soup.select(".card-panel__info li"):
            text = li.get_text(strip=True)
            if "Форма обучения:" in text:
                format_text = text.replace("Форма обучения:", "").strip()
            elif "Режим обучения:" in text:
                study_mode = text.replace("Режим обучения:", "").strip()
            elif "Преподаватели:" in text:
                teachers = text.replace("Преподаватели:", "").strip()
            elif "Дата начала обучения:" in text:
                start_dates = text.replace("Дата начала обучения:", "").strip()
            elif "Продолжительность обучения:" in text:
                duration_weeks = text.replace("Продолжительность обучения:", "").strip()

        # Длительность (часы)
        duration_hours = None
        hours_elem = soup.select_one(".card-panel__note .text-hl-sm span")
        if hours_elem:
            text = hours_elem.get_text(strip=True)
            if "ч." in text:
                try:
                    duration_hours = int(text.replace("ч.", "").strip())
                except ValueError:
                    pass

        # Стоимость
        price = ""
        price_elem = soup.select_one(".card-panel__coll .text-hl-lg")
        if price_elem:
            price = price_elem.get_text(strip=True)

        # Целевая аудитория
        audience_items = soup.select("#courseForWhom .card-rounded__title")
        audience = "\n".join([item.get_text(strip=True) for item in audience_items])

        # Содержание программы
        topics_items = soup.select("#courseProg .list-chat li")
        topics = "\n".join([item.get_text(strip=True) for item in topics_items])

        category_text = course_info.get("category_text", "")

        logger.info(f"  Название: {title}")
        logger.info(f"  Тип программы: {program_type}")
        logger.info(f"  Длительность (часы): {duration_hours}")
        logger.info(f"  Форма: {format_text}")
        logger.info(f"  Стоимость: {price}")

        defaults = {
            "title": title,
            "program_type": program_type,
            "description": description,
            "duration_hours": duration_hours,
            "duration_weeks": duration_weeks,
            "format": format_text,
            "study_mode": study_mode,
            "teachers": teachers,
            "target_audience": audience,
            "topics": topics,
            "price": price,
            "start_dates": start_dates,
            "field_of_study": category_text,
            "organization": self.organization,
        }

        course, created = self._update_course(course_url, defaults)

        if category_text:
            self._assign_categories(course, category_text)

        return course, created
