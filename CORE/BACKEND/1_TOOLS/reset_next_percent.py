import time
import os
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

# Настройки
SETTINGS_PATH = "settings.yaml"
CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
SELL_ON_PERCENT_KEY = "SELL_ON_PERCENT_CHANGE"
LONG_PERCENT_KEY = "NEXT_LONG_PERCENT"
SHORT_PERCENT_KEY = "NEXT_SHORT_PERCENT"
DECIMAL_PLACES = 3

# Логика
def load_yaml_file(file_path):
    """Загружает YAML-файл и возвращает его содержимое."""
    try:
        yaml = YAML(typ='rt')  # rt для сохранения структуры
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.load(file)
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        raise
    except ScannerError as e:
        print(f"Ошибка: Неверный формат YAML в файле {file_path}: {e}")
        raise
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        raise

def save_yaml_file(file_path, data):
    """Сохраняет данные в YAML-файл, сохраняя структуру."""
    try:
        yaml = YAML(typ='rt')
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file)
    except Exception as e:
        print(f"Ошибка при записи файла {file_path}: {e}")
        raise

def update_config():
    """Обновляет переменные в конфигурационном файле на основе настроек."""
    start_time = time.time()
    
    try:
        # Проверка существования файлов
        if not os.path.exists(SETTINGS_PATH):
            print(f"Ошибка: Файл настроек {SETTINGS_PATH} не найден.")
            return
        if not os.path.exists(CONFIG_PATH):
            print(f"Ошибка: Конфигурационный файл {CONFIG_PATH} не найден.")
            return

        # Загрузка настроек
        settings_data = load_yaml_file(SETTINGS_PATH)
        if SELL_ON_PERCENT_KEY not in settings_data:
            print(f"Ошибка: Ключ {SELL_ON_PERCENT_KEY} не найден в {SETTINGS_PATH}.")
            return

        sell_on_percent = float(settings_data[SELL_ON_PERCENT_KEY])
        
        # Загрузка конфигурации
        config_data = load_yaml_file(CONFIG_PATH)
        
        # Проверка наличия ключей в конфигурации
        if LONG_PERCENT_KEY not in config_data:
            print(f"Ошибка: Ключ {LONG_PERCENT_KEY} не найден в {CONFIG_PATH}.")
            return
        if SHORT_PERCENT_KEY not in config_data:
            print(f"Ошибка: Ключ {SHORT_PERCENT_KEY} не найден в {CONFIG_PATH}.")
            return

        # Обновление значений с заданной точностью
        config_data[LONG_PERCENT_KEY] = round(sell_on_percent, DECIMAL_PLACES)
        config_data[SHORT_PERCENT_KEY] = round(-sell_on_percent, DECIMAL_PLACES)

        # Сохранение обновленного конфигурационного файла
        save_yaml_file(CONFIG_PATH, config_data)

        # Вычисление и вывод времени выполнения
        execution_time = time.time() - start_time
        # print(f"Скрипт выполнен за {execution_time:.3f} секунд")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    update_config()