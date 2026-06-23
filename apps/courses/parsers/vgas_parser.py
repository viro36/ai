import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser
from apps.courses.models import Category

logger = logging.getLogger(__name__)


class VgasParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666138230",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКАЯ ГОСУДАРСТВЕННАЯ АКАДЕМИЯ СПОРТА"',
            short_name="ВГАС",
            address_raw="г. Воронеж, ул. Карла Маркса, 59",
        )
        self.BASE_URL = "https://www.vgifk.ru"
        # Создаём категорию при инициализации
        self.sport_category = self._get_or_create_category()

    def _get_or_create_category(self):
        """Создаёт или находит категорию 'Спорт, физическая культура'"""
        category_name = "Спорт, физическая культура"
        category, created = Category.objects.get_or_create(
            name=category_name, defaults={"slug": "sport-fizicheskaya-kultura"}
        )
        if created:
            logger.info(f"Создана категория: {category_name}")
        else:
            logger.info(f"Категория уже существует: {category_name}")
        return category

    def get_courses_list(self):
        """Сбор ссылок на курсы со страницы программ (только ПП и ПК)"""
        courses_data = []

        url = f"{self.BASE_URL}/content/programmy-obucheniya"

        try:
            logger.info(f"Загрузка страницы: {url}")
            response = self.session.get(url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return courses_data

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")

        # --- ТАБЛИЦА 2: профессиональная переподготовка ---
        if len(tables) >= 2:
            pp_table = tables[1]
            pp_rows = pp_table.find_all("tr")

            for row in pp_rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                text = row.get_text(strip=True)
                if (
                    "ПРОФЕССИОНАЛЬНАЯ ПЕРЕПОДГОТОВКА" in text.upper()
                    or "Название" in text
                ):
                    continue

                title = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                if not title or len(title) < 3 or title.isdigit():
                    continue

                price = ""
                if len(cells) > 1:
                    price_text = cells[-1].get_text(strip=True)
                    price_match = re.search(
                        r"(\d+[\s]*\d*)\s*(?:руб|р\.|₽)", price_text
                    )
                    if price_match:
                        price = price_match.group(1).strip() + " руб."

                format_text = "очно-заочная"
                study_mode = "по сб., с применением дистанционных технологий, группа не менее 10 чел."

                slug = re.sub(r"[^a-zA-Zа-яА-Я0-9\s-]", "", title)
                slug = re.sub(r"[-\s]+", "-", slug).strip("-").lower()
                if len(slug) > 50:
                    slug = slug[:50]
                unique_url = f"{url}?course={slug}"

                clean_title = re.sub(r"\s*\([^)]*\)", "", title).strip()

                courses_data.append(
                    {
                        "url": unique_url,
                        "title": clean_title,
                        "program_type": "Профессиональная переподготовка",
                        "price": price,
                        "format_text": format_text,
                        "study_mode": study_mode,
                        "category": self.sport_category,
                    }
                )
                logger.info(f"Найден курс ПП: {clean_title} ({price})")

        # --- ПОВЫШЕНИЕ КВАЛИФИКАЦИИ: таблицы 3, 4, 5 ---
        pk_rows = []
        for i in range(2, min(5, len(tables))):
            table = tables[i]
            rows = table.find_all("tr")
            pk_rows.extend(rows)

        for row in pk_rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            title = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            if not title or len(title) < 3 or title.isdigit():
                continue
            if "Название" in title or "№" in title:
                continue

            duration_hours = None
            if len(cells) > 2:
                hours_text = cells[2].get_text(strip=True)
                hours_match = re.search(r"(\d+)\s*(?:ч|час)", hours_text)
                if hours_match:
                    duration_hours = int(hours_match.group(1))

            price = ""
            if len(cells) > 3:
                price_text = cells[3].get_text(strip=True)
                price_match = re.search(r"(\d+[\s]*\d*)\s*(?:р\.|руб)", price_text)
                if price_match:
                    price = price_match.group(1).strip() + " руб."

            format_text = "очно"
            study_mode = "с пн. по пт., с применением дистанционных технологий, группа не менее 10 чел., возможно обучение по индивидуальному плану"

            slug = re.sub(r"[^a-zA-Zа-яА-Я0-9\s-]", "", title)
            slug = re.sub(r"[-\s]+", "-", slug).strip("-").lower()
            if len(slug) > 50:
                slug = slug[:50]
            unique_url = f"{url}?course={slug}"

            courses_data.append(
                {
                    "url": unique_url,
                    "title": title,
                    "program_type": "Повышение квалификации",
                    "duration_hours": duration_hours,
                    "price": price,
                    "format_text": format_text,
                    "study_mode": study_mode,
                    "category": self.sport_category,
                }
            )
            logger.info(f"Найден курс ПК: {title} ({duration_hours}ч, {price})")

        logger.info(f"Всего найдено курсов ВГАС: {len(courses_data)}")
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
        study_mode = course_info.get("study_mode", "")
        price = course_info.get("price", "")
        category = course_info.get("category")

        base_url = f"{self.BASE_URL}/content/programmy-obucheniya"
        description = ""

        try:
            response = self.session.get(base_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            content_div = soup.select_one(".content")
            if content_div:
                for p in content_div.find_all("p"):
                    text = p.get_text(strip=True)
                    if "Программы" in text and len(text) > 50:
                        description = text
                        break
                if not description:
                    for p in content_div.find_all("p"):
                        text = p.get_text(strip=True)
                        if len(text) > 100 and "КОНТАКТЫ" not in text:
                            description = text
                            break
        except Exception as e:
            logger.error(f"Ошибка загрузки страницы: {e}")

        logger.info(f"  Программа: {title}")
        logger.info(f"    Тип: {program_type}")
        logger.info(f"    Часы: {duration_hours}")
        logger.info(f"    Форма: {format_text}")
        logger.info(f"    Режим: {study_mode}")
        logger.info(f"    Стоимость: {price}")
        logger.info(f"    Категория: {category.name if category else 'Нет'}")

        defaults = {
            "title": title[:500] if title else "",
            "program_type": program_type[:200] if program_type else "",
            "duration_hours": duration_hours,
            "format": format_text[:100] if format_text else "",
            "study_mode": study_mode[:100] if study_mode else "",
            "price": price[:100] if price else "",
            "description": description[:5000] if description else "",
            "field_of_study": "Спорт, физическая культура",
            "target_audience": "Лица, имеющие или получающие среднее профессиональное или высшее образование",
        }

        # Сохраняем курс
        course, created = self._update_course(course_url, defaults)

        # Добавляем категорию
        if course and category:
            course.categories.add(category)
            logger.info(f"  Добавлена категория: {category.name}")

        return course, created
