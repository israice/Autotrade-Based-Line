import sys
import os
import yaml
from datetime import datetime
from typing import Optional
import subprocess
sys.dont_write_bytecode = True

# ==== НАСТРОЙКИ ====
PROJECT_ROOT_LEVELS = 3
FILE_ENCODING = 'utf-8'

# Пути к файлам настроек и данным
SETTINGS_PATH = 'settings.yaml'
A_small_NEW_PATH = 'CORE/DATA/A_small_new_candles_data.yaml'
D_small_OLD_PATH = 'CORE/DATA/D_small_old_candles_data.yaml'
E_large_OLD_PATH = 'CORE/DATA/E_large_old_candles_data.yaml'

# Пути к скриптам для запуска
LARGE_CANDLE_SCRIPT = 'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/CA_check_finish.py'
SMALL_CANDLE_SCRIPT = 'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/CB_check_finish.py'

# ==== ФУНКЦИИ ====
def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *['..'] * PROJECT_ROOT_LEVELS))

def get_yaml_value(yaml_path, key):
    with open(yaml_path, 'r', encoding=FILE_ENCODING) as f:
        data = yaml.safe_load(f)
    return data.get(key)

def get_first_candle_open_time(yaml_path):
    import re
    with open(yaml_path, 'r', encoding=FILE_ENCODING) as f:
        for line in f:
            match = re.match(r"\s*-\s*candle_0_open_time:\s*'([^']+)'", line)
            if match:
                return match.group(1)
    return None

def parse_interval_to_timedelta(interval: str):
    """
    Преобразует строку интервала ('5m', '1h', 'large', '1w', 'small') в (timedelta, 'M' если месяц)
    """
    import re
    match = re.match(r"(\d+)([mhdwM])", interval)
    if not match:
        raise ValueError(f"Некорректный формат интервала: {interval}")
    value, unit = int(match.group(1)), match.group(2)
    if unit == 'm':
        from datetime import timedelta
        return timedelta(minutes=value), None
    elif unit == 'h':
        from datetime import timedelta
        return timedelta(hours=value), None
    elif unit == 'd':
        from datetime import timedelta
        return timedelta(days=value), None
    elif unit == 'w':
        from datetime import timedelta
        return timedelta(weeks=value), None
    elif unit == 'M':
        # Месяцы отдельно
        return None, value
    else:
        raise ValueError(f"Неизвестная единица интервала: {unit}")

def is_interval_passed(time1: str, time2: str, interval: str) -> bool:
    """
    Возвращает True, если разница между time1 и time2 >= interval
    """
    dt1 = datetime.strptime(time1, '%Y-%m-%d %H:%M:%S')
    dt2 = datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
    delta, months = parse_interval_to_timedelta(interval)
    if months is not None:
        # Для месяцев: сравниваем разницу в месяцах
        months_diff = (dt1.year - dt2.year) * 12 + (dt1.month - dt2.month)
        return months_diff >= months
    else:
        return abs(dt1 - dt2) >= delta

def run_script(script_path):
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except KeyboardInterrupt:
        pass
        # Здесь можно добавить дополнительную логику завершения, если нужно
    except Exception as e:
        print(f'Error while running {script_path}: {e}')

# ==== ОСНОВНОЙ КОД ====
project_root = get_project_root()
settings_path = os.path.join(project_root, SETTINGS_PATH)
a_small_new_path = os.path.join(project_root, A_small_NEW_PATH)
d_small_old_path = os.path.join(project_root, D_small_OLD_PATH)
e_large_old_path = os.path.join(project_root, E_large_OLD_PATH)
large_candle_script = os.path.join(project_root, LARGE_CANDLE_SCRIPT)
small_candle_script = os.path.join(project_root, SMALL_CANDLE_SCRIPT)

# Чтение настроек
with open(settings_path, 'r', encoding=FILE_ENCODING) as f:
    settings = yaml.safe_load(f)
sell_interval = settings.get('sell_interval')
buy_interval = settings.get('buy_interval')

# SELL: универсальная проверка по sell_interval
new_candle_time_large = get_first_candle_open_time(a_small_new_path)
old_candle_time_large = get_first_candle_open_time(e_large_old_path)
sell_triggered = False
if new_candle_time_large and old_candle_time_large:
    if is_interval_passed(new_candle_time_large, old_candle_time_large, sell_interval):
        run_script(large_candle_script)
        sell_triggered = True

# Если SELL-логика не сработала, всегда запускаем small_candle_script
if not sell_triggered:
    run_script(small_candle_script)
