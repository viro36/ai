import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser

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

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страницы списка"""
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

                    full_url = self.BASE_URL + link if link.startswith("/") else link

                    courses_data.append(
                        {
                            "url": full_url,
                            "title": title,
                            "category_text": direction,
                        }
                    )
                    logger.info(f"Найден курс: {title}")

                next_link = soup.select_one(".bx-pag-next a")
                if next_link and "href" in next_link.attrs:
                    page_num += 1
                else:
                    break

        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса"""
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

        # Получаем div с деталями
        detail_div = soup.select_one(".program-detail")
        detail_text = detail_div.get_text(separator="\n") if detail_div else ""

        # Извлекаем данные из detail_text
        def extract_value(pattern, text, default=""):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
            return default

        # Форма обучения
        format_text = extract_value(r"Форма обучения:\s*([^\n]+?)(?:\n|$)", detail_text)

        # Продолжительность
        duration_hours = None
        duration_match = re.search(r"Продолжительность:\s*(\d+)\s*часа", detail_text)
        if duration_match:
            duration_hours = int(duration_match.group(1))

        # Стоимость
        price = extract_value(r"Стоимость:\s*([^\n]+?)(?:\n|$)", detail_text)

        # Выдаваемый документ (может быть с переносами и разделителями)
        document_type = ""
        doc_match = re.search(
            r"Выдаваемый документ:\s*([^\n]+?)(?:\n|$)", detail_text, re.DOTALL
        )
        if doc_match:
            document_type = doc_match.group(1).strip()

        # Если не нашли через регулярку, пробуем найти в HTML
        if not document_type:
            doc_elem = soup.find(string=re.compile(r"Выдаваемый документ:"))
            if doc_elem:
                parent = doc_elem.parent
                # Ищем следующий элемент после "Выдаваемый документ:"
                next_elem = parent.find_next_sibling()
                if next_elem:
                    document_type = next_elem.get_text(strip=True)
                else:
                    # Или текст внутри родителя
                    full_text = parent.get_text(strip=True)
                    match = re.search(r"Выдаваемый документ:\s*(.+)", full_text)
                    if match:
                        document_type = match.group(1).strip()

        # Описание
        description = ""
        desc_match = re.search(
            r"Описание:\s*\n?\s*(.*?)(?=\n\s*\n\s*Ключевые особенности|\n\s*\n\s*Категория слушателей|\n\s*\n\s*Требования|\Z)",
            detail_text,
            re.DOTALL,
        )
        if desc_match:
            description = desc_match.group(1).strip()
            description = re.sub(r"\n+", "\n", description)
            description = description[:5000]

        # Преподаватели
        teachers = ""
        teacher_match = re.search(
            r"([А-Я][а-я]+\s+[А-Я][а-я]+(?:\s+[А-Я][а-я]+)?)\s*\n\s*(?:Доцент|Профессор)",
            detail_text,
        )
        if teacher_match:
            teachers = teacher_match.group(1).strip()

        # Если не нашли через регулярку, ищем в HTML
        if not teachers:
            teacher_elem = soup.select_one(".name-teach b")
            if teacher_elem:
                teachers = teacher_elem.get_text(strip=True)

        category_text = course_info.get("category_text", "")

        logger.info(f"  Название: {title}")
        logger.info(f"  Длительность (часы): {duration_hours}")
        logger.info(f"  Форма: {format_text}")
        logger.info(f"  Стоимость: {price}")
        logger.info(f"  Документ: {document_type}")
        logger.info(f"  Преподаватели: {teachers}")

        # Собираем только непустые данные
        defaults = {
            "title": title,
            "description": description,
            "duration_hours": duration_hours,
            "format": format_text,
            "price": price,
            "teachers": teachers,
            "document_type": document_type,
            "field_of_study": category_text,
        }

        return self._update_course(course_url, defaults)
