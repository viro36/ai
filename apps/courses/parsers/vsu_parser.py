import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VsuParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666029505",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ"',
            short_name="ВГУ",
            address_raw="г. Воронеж, Университетская площадь, 1",
        )
        self.BASE_URL = "https://pdi.vsu.ru"

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страницы списка"""
        courses_data = []
        url = f"{self.BASE_URL}/services.php"

        try:
            logger.info(f"Загрузка страницы: {url}")
            response = self.session.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return courses_data

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.table tbody tr")

        logger.info(f"Найдено строк в таблице: {len(rows)}")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 14:
                continue

            title = cells[0].get_text(strip=True)
            if not title:
                continue

            direction = cells[4].get_text(strip=True) if len(cells) > 4 else ""

            link_cell = cells[13] if len(cells) > 13 else None
            if not link_cell:
                continue

            link_tag = link_cell.find("a")
            if not link_tag:
                continue

            link = link_tag.get("href")
            if not link or link == "#":
                continue

            if link.startswith("/"):
                full_url = self.BASE_URL + link
            elif link.startswith("http"):
                full_url = link
            else:
                full_url = self.BASE_URL + "/" + link

            courses_data.append(
                {
                    "url": full_url,
                    "title": title,
                    "category_text": direction,
                    "program_type": (
                        cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    ),
                    "duration_hours_text": (
                        cells[7].get_text(strip=True) if len(cells) > 7 else ""
                    ),
                    "duration_months": (
                        cells[8].get_text(strip=True) if len(cells) > 8 else ""
                    ),
                    "format_text": (
                        cells[6].get_text(strip=True) if len(cells) > 6 else ""
                    ),
                    "price": cells[9].get_text(strip=True) if len(cells) > 9 else "",
                    "target_audience": (
                        cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    ),
                    "teachers": (
                        cells[12].get_text(strip=True) if len(cells) > 12 else ""
                    ),
                    "document_type": (
                        cells[10].get_text(strip=True) if len(cells) > 10 else ""
                    ),
                }
            )
            logger.info(f"Найден курс: {title} -> {full_url}")

        logger.info(f"Всего найдено курсов: {len(courses_data)}")
        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса"""
        course_url = course_info.get("url")

        if not course_url:
            logger.error("Пустой URL курса")
            return None, False

        title = course_info.get("title", "")
        program_type = course_info.get("program_type", "")

        duration_hours = None
        duration_text = course_info.get("duration_hours_text", "")
        if duration_text:
            match = re.search(r"(\d+)\s*ч", duration_text)
            if match:
                duration_hours = int(match.group(1))

        format_text = course_info.get("format_text", "")
        price = course_info.get("price", "")
        if price == "-" or price == "NA":
            price = ""

        category_text = course_info.get("category_text", "")
        target_audience = course_info.get("target_audience", "")
        teachers = course_info.get("teachers", "")
        document_type = course_info.get("document_type", "")

        logger.info(f"  Название: {title}")
        logger.info(f"  Тип программы: {program_type}")
        logger.info(f"  Длительность (часы): {duration_hours}")
        logger.info(f"  Форма: {format_text}")
        logger.info(f"  Стоимость: {price}")

        # Собираем defaults (organization передаётся отдельно)
        defaults = {
            "title": title,
            "program_type": program_type,
            "duration_hours": duration_hours,
            "format": format_text,
            "price": price,
            "field_of_study": category_text,
            "target_audience": target_audience,
            "teachers": teachers,
            "document_type": document_type,
        }

        # Обновляем курс через метод, который гарантирует установку организации
        course, created = self._update_course(course_url, defaults)

        # Привязываем категории
        if category_text:
            self._assign_categories(course, category_text)

        return course, created
