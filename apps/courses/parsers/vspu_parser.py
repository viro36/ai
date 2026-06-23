import logging
import re
from bs4 import BeautifulSoup
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class VspuParser(BaseParser):
    def __init__(self):
        super().__init__(
            inn="3666008174",
            full_name='ФГБОУ ВО "ВОРОНЕЖСКИЙ ГОСУДАРСТВЕННЫЙ ПЕДАГОГИЧЕСКИЙ УНИВЕРСИТЕТ"',
            short_name="ВГПУ",
            address_raw="г. Воронеж, ул. Ленина, 86",
        )
        self.BASE_URL = "http://dopobr.vspu.ac.ru"

    def get_courses_list(self):
        """Сбор ссылок на ВСЕ курсы со страницы категорий"""
        courses_data = []

        main_url = f"{self.BASE_URL}/all-programs/"

        try:
            logger.info(f"Загрузка главной страницы: {main_url}")
            response = self.session.get(main_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка при загрузке {main_url}: {e}")
            return courses_data

        soup = BeautifulSoup(response.text, "html.parser")

        # Находим все карточки с программами
        cards = soup.select(".elementor-cta")

        for card in cards:
            link_elem = card.select_one(".elementor-cta__button")
            if not link_elem:
                continue

            href = link_elem.get("href")
            if not href or href == "#":
                continue

            title_elem = card.select_one(".elementor-cta__title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = self.BASE_URL + href
            else:
                full_url = self.BASE_URL + "/" + href

            courses_data.append(
                {
                    "url": full_url,
                    "title": title,
                    "category_text": title,
                }
            )
            logger.info(f"Найдена категория: {title} -> {full_url}")

        logger.info(f"Всего найдено категорий: {len(courses_data)}")
        return courses_data

    def parse_course_detail(self, course_info):
        """Парсинг страницы категории с программами и детальных страниц"""
        category_url = course_info.get("url")
        category_title = course_info.get("title", "")

        if not category_url:
            logger.error("Пустой URL")
            return None, False

        try:
            logger.info(f"Загрузка страницы категории: {category_url}")
            response = self.session.get(category_url, headers=self.HEADERS, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Ошибка загрузки {category_url}: {e}")
            return None, False

        soup = BeautifulSoup(response.text, "html.parser")

        # Находим все виджеты price-table (это отдельные программы)
        price_tables = soup.select(".elementor-price-table")

        created_count = 0
        updated_count = 0

        for table in price_tables:
            # Название программы
            title_elem = table.select_one(".elementor-price-table__heading")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Подзаголовок (тип программы)
            subtitle_elem = table.select_one(".elementor-price-table__subheading")
            program_type = subtitle_elem.get_text(strip=True) if subtitle_elem else ""

            # Стоимость
            price_elem = table.select_one(".elementor-price-table__integer-part")
            price = price_elem.get_text(strip=True) if price_elem else ""

            # Ссылка "Узнать подробнее"
            button = table.select_one(".elementor-price-table__button")
            detail_url = button.get("href") if button else None

            # Характеристики (список)
            features = []
            for li in table.select(".elementor-price-table__features-list li"):
                span = li.select_one("span")
                if span:
                    features.append(span.get_text(strip=True))

            # Парсим длительность и документ из features
            duration_hours = None
            document_type = ""
            target_audience = ""

            for feature in features:
                if "Продолжительность" in feature or "часов" in feature:
                    hours_match = re.search(r"(\d+)\s*(?:часа|часов|ч)", feature)
                    if hours_match:
                        duration_hours = int(hours_match.group(1))
                    if "/" in feature:
                        hours_match = re.search(r"(\d+)\s*/\s*(\d+)", feature)
                        if hours_match:
                            duration_hours = int(hours_match.group(1))
                if "Документ" in feature:
                    document_type = feature.replace("Документ:", "").strip()
                if "Целевая аудитория" in feature:
                    target_audience = feature.replace("Целевая аудитория:", "").strip()

            if not title:
                continue

            if not detail_url:
                detail_url = category_url

            # Получаем полный URL
            if detail_url.startswith("http"):
                full_url = detail_url
            elif detail_url.startswith("/"):
                full_url = self.BASE_URL + detail_url
            else:
                full_url = self.BASE_URL + "/" + detail_url

            # Парсим детальную страницу
            description = ""
            topics = ""

            if full_url:
                try:
                    logger.info(f"  Загрузка детальной страницы: {full_url}")
                    detail_response = self.session.get(
                        full_url, headers=self.HEADERS, timeout=30
                    )
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                    content_div = detail_soup.select_one(".entry-content")
                    if content_div:
                        # Получаем весь текст
                        all_text = content_div.get_text(separator="\n")

                        # Ищем описание (первый абзац с "Целью")
                        desc_match = re.search(
                            r"Цель.*?(?=\n\s*\n\s*\n|Продолжительность|Документ|Целевая|Содержание|Результаты)",
                            all_text,
                            re.DOTALL | re.IGNORECASE,
                        )
                        if desc_match:
                            description = desc_match.group(0).strip()
                        else:
                            # Ищем любой абзац с "формирование" или "компетенций"
                            for p in content_div.select("p"):
                                text = p.get_text(strip=True)
                                if (
                                    "формирование" in text.lower()
                                    or "компетенций" in text.lower()
                                ):
                                    description = text
                                    break

                        # Ищем содержание программы
                        topics_match = re.search(
                            r"Содержание программы:.*?(?=\n\s*\n\s*\n|Результаты обучения|Стоимость|$)",
                            all_text,
                            re.DOTALL | re.IGNORECASE,
                        )
                        if topics_match:
                            topics = topics_match.group(0).strip()
                            # Убираем заголовок "Содержание программы:"
                            topics = re.sub(r"Содержание программы:?\s*", "", topics)

                        # Если не нашли через regex, пробуем через HTML
                        if not topics:
                            for ul in content_div.select("ul"):
                                # Проверяем, что это список содержания
                                prev = ul.find_previous_sibling()
                                if prev and "Содержание" in prev.get_text():
                                    topics_list = []
                                    for li in ul.select("li"):
                                        topics_list.append(li.get_text(strip=True))
                                    topics = "\n".join(topics_list)
                                    break

                        # Если всё равно нет, берём все списки
                        if not topics:
                            topics_list = []
                            for ul in content_div.select("ul"):
                                for li in ul.select("li"):
                                    text = li.get_text(strip=True)
                                    if text and len(text) > 5:
                                        topics_list.append(text)
                            if topics_list:
                                topics = "\n".join(topics_list)

                        logger.info(f"    Описание: {len(description)} символов")
                        logger.info(f"    Содержание: {len(topics)} символов")

                except Exception as e:
                    logger.error(
                        f"  Ошибка загрузки детальной страницы {full_url}: {e}"
                    )

            logger.info(f"  Программа: {title}")
            logger.info(f"    Тип: {program_type}")
            logger.info(f"    Часы: {duration_hours}")
            logger.info(f"    Стоимость: {price}")
            logger.info(f"    Документ: {document_type}")

            defaults = {
                "title": title[:500],
                "program_type": program_type[:200] if program_type else "",
                "duration_hours": duration_hours,
                "price": price[:100] if price else "",
                "document_type": document_type[:200] if document_type else "",
                "target_audience": target_audience[:2000] if target_audience else "",
                "field_of_study": category_title[:500],
                "description": description[:5000] if description else "",
                "topics": topics[:10000] if topics else "",
            }

            if full_url:
                course, created = self._update_course(full_url, defaults)
                if created:
                    created_count += 1
                    logger.info(f"Создан курс: {title}")
                else:
                    updated_count += 1
                    logger.info(f"Обновлён курс: {title}")
            else:
                logger.error(f"Нет URL для программы {title}")

        logger.info(
            f"Сохранено программ: создано {created_count}, обновлено {updated_count}"
        )

        return {"created": created_count, "updated": updated_count}
