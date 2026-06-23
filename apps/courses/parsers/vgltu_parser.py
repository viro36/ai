import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VgltuParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666012325",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКИЙ ГОСУДАРСТВЕННЫЙ ЛЕСОТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ"',
            short_name="ВГЛТУ",
            address_raw="г. Воронеж, ул. Тимирязева, 8",
        )
        self.BASE_URL = "https://vgltu.ru"

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страниц вкладок"""
        courses_data = []

        tabs = [
            (
                "/universitet/podrazdeleniya/centr-dopolnitelnogo-professionalnogo-obrazovaniya/professionalnaya-perepodgotovka/",
                "Профессиональная переподготовка",
            ),
            (
                "/universitet/podrazdeleniya/centr-dopolnitelnogo-professionalnogo-obrazovaniya/povyshenie-kvalifikacii/",
                "Повышение квалификации",
            ),
            (
                "/universitet/podrazdeleniya/centr-dopolnitelnogo-professionalnogo-obrazovaniya/professionalnoe-obuchenie/",
                "Профессиональное обучение",
            ),
        ]

        for tab_url, program_type in tabs:
            full_url = self.BASE_URL + tab_url

            try:
                logger.info(f"Загрузка страницы: {full_url}")
                response = self.session.get(full_url, headers=self.HEADERS, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Ошибка при загрузке {full_url}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select(".parent")

            for card in cards:
                link = card.get("href")
                if not link:
                    continue

                if link.startswith("/"):
                    full_link = self.BASE_URL + link
                elif link.startswith("http"):
                    full_link = link
                else:
                    full_link = self.BASE_URL + "/" + link

                title_elem = card.select_one("h4")
                title = title_elem.get_text(strip=True) if title_elem else ""

                cat_elem = card.select_one("div[style*='font-size: 12px']")
                category_text = cat_elem.get_text(strip=True) if cat_elem else ""

                hours_elem = card.select_one(
                    ".parent .vv2-wrapper, .parent div:has(img[src*='vv2']) + p"
                )
                duration_hours = None
                if hours_elem:
                    hours_text = hours_elem.get_text(strip=True)
                    hours_match = re.search(r"(\d+)\s*(?:часа|часов|ч)", hours_text)
                    if hours_match:
                        duration_hours = int(hours_match.group(1))

                format_elem = card.select_one(
                    ".parent .vh1-wrapper, .parent div:has(img[src*='vh1']) + p"
                )
                format_text = format_elem.get_text(strip=True) if format_elem else ""

                price_elem = card.select_one(
                    ".parent div[style*='font-weight: bold; font-size: 30px;']"
                )
                price = price_elem.get_text(strip=True) if price_elem else ""

                courses_data.append(
                    {
                        "url": full_link,
                        "title": title,
                        "category_text": category_text,
                        "program_type": program_type,
                        "duration_hours": duration_hours,
                        "format_text": format_text,
                        "price": price,
                    }
                )
                logger.info(f"Найден курс: {title} ({program_type})")

        logger.info(f"Всего найдено курсов ВГЛТУ: {len(courses_data)}")
        return courses_data

    def _get_content_div(self, soup):
        """Находит правильный div.content с контентом курса"""
        all_content = soup.find_all("div", class_="content")

        for div in all_content:
            text = div.get_text(strip=True)
            # Ищем div с признаками контента курса
            if "Цель" in text or "Программа обучения" in text or "Для кого" in text:
                return div

        # Если не нашли по признакам, берём последний div.content
        if all_content:
            return all_content[-1]

        return None

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

        # Находим правильный div.content
        content_div = self._get_content_div(soup)

        if not content_div:
            logger.error("Контент не найден")
            defaults = {
                "title": course_info.get("title", "")[:500],
                "program_type": course_info.get("program_type", "")[:200],
                "duration_hours": course_info.get("duration_hours"),
                "format": course_info.get("format_text", "")[:100],
                "price": course_info.get("price", "")[:100],
                "field_of_study": course_info.get("category_text", "")[:500],
            }
            course, created = self._update_course(course_url, defaults)
            # Привязываем категории, даже если контент не найден
            if course_info.get("category_text"):
                self._assign_categories(course, course_info["category_text"])
            return course, created

        # ========== НАЗВАНИЕ ==========
        title = course_info.get("title", "")
        h2_title = content_div.find("h2")
        if h2_title:
            title = h2_title.get_text(strip=True)

        # ========== ОПИСАНИЕ ==========
        description = ""
        for p in content_div.find_all("p"):
            text = p.get_text(strip=True)
            if "Цель" in text and len(text) > 30:
                description = text
                break

        if not description:
            for p in content_div.find_all("p"):
                text = p.get_text(strip=True)
                if (
                    len(text) > 50
                    and "Режим работы" not in text
                    and "Контакты" not in text
                ):
                    description = text
                    break

        logger.info(
            f"  Найдено описание: {description[:100] if description else 'НЕТ'}..."
        )

        # ========== СОДЕРЖАНИЕ ПРОГРАММЫ ==========
        topics = ""
        for h2 in content_div.find_all("h2"):
            if "Программа обучения" in h2.get_text():
                for sibling in h2.find_next_siblings():
                    if sibling.name == "h2":
                        break
                    if sibling.name == "ul":
                        items = []
                        for li in sibling.find_all("li"):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                items.append(li_text)
                        if items:
                            topics += "\n".join(items) + "\n"
                break

        if not topics:
            for ul in content_div.find_all("ul"):
                items = []
                for li in ul.find_all("li"):
                    li_text = li.get_text(strip=True)
                    if li_text and (
                        "Модуль" in li_text or "1." in li_text or "2." in li_text
                    ):
                        items.append(li_text)
                if len(items) > 2:
                    topics = "\n".join(items)
                    break

        logger.info(f"  Найдено содержание: {topics[:100] if topics else 'НЕТ'}...")

        # ========== ЦЕЛЕВАЯ АУДИТОРИЯ ==========
        target_audience = ""
        for h2 in content_div.find_all("h2"):
            if "Для кого" in h2.get_text():
                ul = h2.find_next_sibling("ul")
                if ul:
                    items = []
                    for li in ul.find_all("li"):
                        li_text = li.get_text(strip=True)
                        if li_text:
                            items.append(li_text)
                    target_audience = "\n".join(items)
                break

        # ========== УСЛОВИЯ ПРИЁМА ==========
        for h4 in content_div.find_all("h4"):
            if "Условия приема" in h4.get_text():
                parent = h4.find_parent()
                if parent:
                    p = parent.find("p")
                    if p:
                        conditions = p.get_text(strip=True)
                        if target_audience:
                            target_audience += "\n\nУсловия приема: " + conditions
                        else:
                            target_audience = "Условия приема: " + conditions
                break

        # ========== ДЛИТЕЛЬНОСТЬ ==========
        duration_hours = course_info.get("duration_hours")
        if not duration_hours:
            for h4 in content_div.find_all("h4"):
                if "Продолжительность" in h4.get_text():
                    parent = h4.find_parent()
                    if parent:
                        p = parent.find("p")
                        if p:
                            hours_match = re.search(
                                r"(\d+)\s*(?:часа|часов|ч)", p.get_text(strip=True)
                            )
                            if hours_match:
                                duration_hours = int(hours_match.group(1))

        # ========== ФОРМАТ ОБУЧЕНИЯ ==========
        format_text = course_info.get("format_text", "")
        if not format_text:
            for h4 in content_div.find_all("h4"):
                if "Форма обучения" in h4.get_text():
                    parent = h4.find_parent()
                    if parent:
                        p = parent.find("p")
                        if p:
                            format_text = p.get_text(strip=True)

        # ========== СТОИМОСТЬ ==========
        price = course_info.get("price", "")
        if not price:
            for h4 in content_div.find_all("h4"):
                if "Стоимость" in h4.get_text():
                    parent = h4.find_parent()
                    if parent:
                        h2 = parent.find("h2")
                        if h2:
                            price = h2.get_text(strip=True)

        # ========== ДОКУМЕНТ ==========
        document_type = ""
        for h2 in content_div.find_all("h2"):
            if "Документ об окончании" in h2.get_text():
                parent = h2.find_next_sibling()
                if parent:
                    p = parent.find("p")
                    if p:
                        document_type = p.get_text(strip=True)
                    else:
                        document_type = parent.get_text(strip=True)
                break

        # ========== ПРЕПОДАВАТЕЛИ ==========
        teachers = ""
        for h2 in content_div.find_all("h2"):
            if "Руководитель курса" in h2.get_text():
                parent = h2.find_next_sibling()
                if parent:
                    h4 = parent.find("h4")
                    if h4:
                        teachers = h4.get_text(strip=True)
                break

        program_type = course_info.get("program_type", "")
        category_text = course_info.get("category_text", "")

        logger.info(f"  Название: {title}")
        logger.info(f"  Тип программы: {program_type}")
        logger.info(f"  Длительность (часы): {duration_hours}")
        logger.info(f"  Форма: {format_text}")
        logger.info(f"  Стоимость: {price}")
        logger.info(f"  Документ: {document_type}")
        logger.info(f"  Преподаватели: {teachers}")
        logger.info(f"  Описание: {len(description)} символов")
        logger.info(f"  Содержание: {len(topics)} символов")
        logger.info(f"  Целевая аудитория: {len(target_audience)} символов")
        logger.info(f"  Категории: {category_text}")

        defaults = {
            "title": title[:500] if title else "",
            "description": description[:5000] if description else "",
            "program_type": program_type[:200] if program_type else "",
            "duration_hours": duration_hours,
            "format": format_text[:100] if format_text else "",
            "price": price[:100] if price else "",
            "teachers": teachers[:500] if teachers else "",
            "topics": topics[:10000] if topics else "",
            "target_audience": target_audience[:2000] if target_audience else "",
            "document_type": document_type[:200] if document_type else "",
            "field_of_study": category_text[:500] if category_text else "",
        }

        course, created = self._update_course(course_url, defaults)

        # ========== ПРИВЯЗКА КАТЕГОРИЙ ==========
        if category_text:
            self._assign_categories(course, category_text)

        return course, created
