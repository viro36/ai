import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VepiParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666134884",
            full_name='АНОО ВО "ВОРОНЕЖСКИЙ ЭКОНОМИКО-ПРАВОВОЙ ИНСТИТУТ"',
            short_name="ВЭПИ",
            address_raw="г. Воронеж, Ленинский проспект, 119А",
        )
        self.BASE_URL = "https://vepi.ru"

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страниц программ"""
        courses_data = []

        # Страницы с программами
        pages = [
            "/abitur/programmy-professionalnoj-perepodgotovki/",
            "/abitur/programmy-povysheniya-kvalifikatsii/",
            "/abitur/dopolnitelnoe-obrazovanie-detej-i-vzroslyh/",
        ]

        program_type_map = {
            "/abitur/programmy-professionalnoj-perepodgotovki/": "Профессиональная переподготовка",
            "/abitur/programmy-povysheniya-kvalifikatsii/": "Повышение квалификации",
            "/abitur/dopolnitelnoe-obrazovanie-detej-i-vzroslyh/": "Дополнительное образование",
        }

        for page in pages:
            full_url = self.BASE_URL + page
            program_type = program_type_map.get(page, "")

            try:
                logger.info(f"Загрузка страницы: {full_url}")
                response = self.session.get(full_url, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Ошибка при загрузке {full_url}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Находим таблицу с программами
            table = soup.select_one(".scrolltable4")
            if not table:
                logger.warning(f"Таблица не найдена на {page}")
                continue

            # Находим все строки с программами
            rows = table.select(".row.planrabot2")

            for row in rows:
                # Название и ссылка
                link_elem = row.select_one("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                href = link_elem.get("href")

                if not href or href == "#":
                    continue

                # Полный URL
                if href.startswith("http"):
                    full_link = href
                elif href.startswith("/"):
                    full_link = self.BASE_URL + href
                else:
                    full_link = self.BASE_URL + "/" + href

                # Парсим колонки таблицы
                cols = row.select(
                    ".col-md-1, .col-md-2, .col-md-3, .col-1, .col-2, .col-3"
                )

                duration_hours = None
                document_type = ""
                price = ""
                teachers = ""

                for i, col in enumerate(cols):
                    text = col.get_text(strip=True)
                    if i == 2:  # Трудоемкость (часы)
                        if text.isdigit():
                            duration_hours = int(text)
                    elif i == 4:  # Выдаваемый документ
                        if "Диплом" in text or "Удостоверение" in text:
                            document_type = text
                    elif i == 5:  # Руководитель обучения (преподаватель)
                        if text and text != "-":
                            teachers = text
                    elif i == 6:  # Стоимость
                        if text and text != "-":
                            price = text

                # Если не нашли, пробуем по регулярке
                if not duration_hours:
                    hours_match = re.search(r"(\d+)\s*ч", str(row))
                    if hours_match:
                        duration_hours = int(hours_match.group(1))

                if not document_type:
                    doc_match = re.search(
                        r"(Диплом|Удостоверение).*?переподготовк|квалификац",
                        str(row),
                        re.IGNORECASE,
                    )
                    if doc_match:
                        document_type = doc_match.group(0).strip()

                courses_data.append(
                    {
                        "url": full_link,
                        "title": title,
                        "program_type": program_type,
                        "duration_hours": duration_hours,
                        "document_type": document_type,
                        "price": price,
                        "teachers": teachers,
                        "category_text": program_type,
                    }
                )
                logger.info(f"Найден курс: {title} ({program_type})")

        logger.info(f"Всего найдено курсов ВЭПИ: {len(courses_data)}")
        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг детальной страницы курса"""
        course_url = course_info.get("url")

        if not course_url:
            logger.error("Пустой URL")
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
        title_elem = soup.select_one("h1")
        title = (
            title_elem.get_text(strip=True)
            if title_elem
            else course_info.get("title", "")
        )

        # Парсим таблицу на детальной странице
        description = ""
        topics = ""
        target_audience = ""
        format_text = ""
        study_mode = ""
        duration_hours = course_info.get("duration_hours")
        document_type = course_info.get("document_type", "")
        price = course_info.get("price", "")
        program_type = course_info.get("program_type", "")
        teachers = course_info.get("teachers", "")

        table = soup.select_one(".tblock table")
        if table:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td")
                if not th or not td:
                    continue

                header = th.get_text(strip=True)
                content = td.get_text(strip=True)

                if "Категории обучающихся" in header:
                    target_audience = content
                elif "Востребованность" in header:
                    if target_audience:
                        target_audience += "\n\n" + content
                    else:
                        target_audience = content
                elif "Длительность обучения" in header or "Продолжительность" in header:
                    hours_match = re.search(r"(\d+)\s*часов", content)
                    if hours_match:
                        duration_hours = int(hours_match.group(1))
                elif "Форма обучения" in header:
                    # Парсим li напрямую через BeautifulSoup
                    li_items = td.select("li")
                    if li_items:
                        # Первая li — Форма обучения
                        format_text = (
                            li_items[0]
                            .get_text(strip=True)
                            .replace(";", "")
                            .strip()[:100]
                        )
                        # Вторая li — Режим обучения (если есть)
                        study_mode = (
                            li_items[1]
                            .get_text(strip=True)
                            .replace(";", "")
                            .strip()[:100]
                            if len(li_items) > 1
                            else ""
                        )
                    else:
                        # Если li нет, пробуем старый способ
                        lines = [
                            re.sub(r"^[•\-0-9.]\s*", "", line.strip())
                            for line in content.split("\n")
                            if line.strip()
                        ]
                        if lines:
                            format_text = lines[0][:100]
                            study_mode = lines[1][:100] if len(lines) > 1 else ""
                        else:
                            format_text = content[:100]
                            study_mode = ""
                elif "Цель" in header:
                    description = content
                elif "Задачи" in header:
                    topics = content
                elif "Прогнозируемые результаты" in header:
                    if topics:
                        topics += "\n\n" + content
                    else:
                        topics = content
                elif "Выдаваемый документ" in header:
                    document_type = content
                elif "Руководитель" in header:
                    teachers = content

        # Если не нашли описание в таблице
        if not description:
            for elem in soup.select(".tblock p, .tblock div"):
                text = elem.get_text(strip=True)
                if "формирование" in text.lower() or "компетенций" in text.lower():
                    description = text
                    break

        # Если не нашли topics
        if not topics:
            for ul in soup.select("ul.spis"):
                items = []
                for li in ul.select("li"):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        items.append(li_text)
                if items:
                    topics = "\n".join(items)
                    break

        logger.info(f"  Программа: {title}")
        logger.info(f"    Тип: {program_type}")
        logger.info(f"    Часы: {duration_hours}")
        logger.info(f"    Форма обучения: {format_text}")
        logger.info(f"    Режим обучения: {study_mode}")
        logger.info(f"    Стоимость: {price}")
        logger.info(f"    Документ: {document_type}")
        logger.info(f"    Преподаватели: {teachers}")
        logger.info(f"    Описание: {len(description)} символов")
        logger.info(f"    Содержание: {len(topics)} символов")
        logger.info(f"    Целевая аудитория: {len(target_audience)} символов")

        defaults = {
            "title": title[:500],
            "program_type": program_type[:200] if program_type else "",
            "duration_hours": duration_hours,
            "format": format_text[:100] if format_text else "",
            "study_mode": study_mode[:100] if study_mode else "",
            "price": price[:100] if price else "",
            "document_type": document_type[:200] if document_type else "",
            "teachers": teachers[:500] if teachers else "",
            "target_audience": target_audience[:2000] if target_audience else "",
            "description": description[:5000] if description else "",
            "topics": topics[:10000] if topics else "",
            "field_of_study": program_type[:500],
        }

        return self._update_course(course_url, defaults)
