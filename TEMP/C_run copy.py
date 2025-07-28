
# ================= ЧТО ДЕЛАЕТ СКРИПТ =================
# сравниваем разнцу во времени между новым и старым 
# индикация что свеча завершилась
# =====================================================

import sys
import os
import yaml
import subprocess
sys.dont_write_bytecode = True

# ==== НАСТРОЙКИ ====
PROJECT_ROOT_LEVELS_UP = 3  # сколько уровней вверх от текущего файла до корня проекта
YAML_NEW_CANDLE_REL_PATH = 'CORE/DATA/A_small_new_candles_data.yaml'  # путь к файлу новых свечей (от корня)
YAML_OLD_CANDLE_REL_PATH = 'CORE/DATA/E_small_old_candles_data.yaml'  # путь к файлу старых свечей (от корня)
CANDLE_OPEN_TIME_KEY = 'candle_0_open_time'  # ключ времени открытия свечи
YAML_ENCODING = 'utf-8'  # кодировка yaml-файлов
SCRIPTS = [  # список скриптов, которые нужно запускать при смене свечи
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large_candle/CA_large.py',
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small_candle/CB_small.py',
]

# ==== ОСНОВНОЙ КОД ====
def get_candle_0_open_time(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        # Если это список, берем первый словарь
        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
            if isinstance(entry, dict):
                return entry.get('candle_0_open_time')
        elif isinstance(data, dict):
            return data.get('candle_0_open_time')
    return None

def is_null(val):
    return val is None or str(val).strip().lower() in ("", "none", "null")


# ==== ОСНОВНОЙ КОД ====
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * PROJECT_ROOT_LEVELS_UP)))
file_new_candle = os.path.join(project_root, YAML_NEW_CANDLE_REL_PATH)
file_old_candle = os.path.join(project_root, YAML_OLD_CANDLE_REL_PATH)

def get_candle_0_open_time(yaml_path):
    with open(yaml_path, 'r', encoding=YAML_ENCODING) as f:
        data = yaml.safe_load(f)
        if isinstance(data, list) and len(data) > 0:
            entry = data[0]
            if isinstance(entry, dict):
                return entry.get(CANDLE_OPEN_TIME_KEY)
        elif isinstance(data, dict):
            return data.get(CANDLE_OPEN_TIME_KEY)
    return None

def is_null(val):
    return val is None or str(val).strip().lower() in ("", "none", "null")

candle1 = get_candle_0_open_time(file_new_candle)
candle2 = get_candle_0_open_time(file_old_candle)

if not is_null(candle1) and not is_null(candle2) and candle1 != candle2:
    for script_rel_path in SCRIPTS:
        script_path = os.path.join(project_root, script_rel_path)
        if os.path.exists(script_path):
            subprocess.run([sys.executable, script_path], check=True)
        else:
            print(f"Файл {script_path} не найден!")
