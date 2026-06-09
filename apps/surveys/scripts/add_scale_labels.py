#!/usr/bin/env python
"""Скрипт для добавления глобальных формулировок шкалы"""

import os
import sys

# Добавляем путь к проекту (корневая директория)
BASE_DIR = "/App"
sys.path.insert(0, BASE_DIR)

# Указываем настройки проекта
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai.settings")

# Инициализируем Django
import django

django.setup()

from apps.surveys.models import ScaleLabel


def add_global_scale_labels():
    """Добавление глобальных формулировок шкалы"""

    default_labels = {
        1: "совсем не соответствует / не умею / никогда не делаю",
        2: "скорее не соответствует / редко делаю / испытываю трудности",
        3: "частично соответствует / иногда делаю / с помощью подсказок",
        4: "в основном соответствует / часто делаю / уверенно",
        5: "полностью соответствует / регулярно делаю / очень уверенно",
    }

    print("\n" + "=" * 60)
    print("Добавление глобальных формулировок шкалы")
    print("=" * 60 + "\n")

    for score, label in default_labels.items():
        obj, created = ScaleLabel.objects.get_or_create(
            category=None, scale_value=score, defaults={"label": label}
        )
        action = "Создана" if created else "Уже существует"
        print(f"{action} формулировка для {score} баллов: {label[:50]}...")

    print("\n" + "=" * 60)
    print("Глобальные формулировки шкалы добавлены!")
    print("=" * 60)


if __name__ == "__main__":
    add_global_scale_labels()
