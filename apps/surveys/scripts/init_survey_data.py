import os
import sys
import subprocess


def run_script(script_name):
    """Запуск скрипта"""
    result = subprocess.run(
        [sys.executable, script_name], capture_output=False, text=True
    )
    return result.returncode


def main():
    print("\n" + "=" * 70)
    print("ИНИЦИАЛИЗАЦИЯ ДАННЫХ ДЛЯ ОПРОСОВ")
    print("=" * 70)

    # Получаем путь к директории скриптов
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Добавляем глобальные формулировки шкалы
    print("\n Шаг 1: Добавление глобальных формулировок шкалы")
    print("-" * 50)
    run_script(os.path.join(scripts_dir, "add_scale_labels.py"))

    # 2. Добавляем инструкции и описания
    print("\n Шаг 2: Добавление инструкций и описаний результатов")
    print("-" * 50)
    run_script(os.path.join(scripts_dir, "add_survey_descriptions.py"))

    # 3. Добавляем уровни
    print("\n Шаг 3: Добавление уровней")
    print("-" * 50)
    run_script(os.path.join(scripts_dir, "load_survey_data.py"))

    print("\n" + "=" * 70)
    print("Инициализация данных завершена!")
    print("=" * 70)


if __name__ == "__main__":
    main()
