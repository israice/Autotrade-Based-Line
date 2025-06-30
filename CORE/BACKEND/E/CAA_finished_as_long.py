import sys
import os
import yaml
import subprocess

sys.dont_write_bytecode = True

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

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
file1 = os.path.join(project_root, 'CORE/DATA/A_fetch_candles.yaml')
file2 = os.path.join(project_root, 'CORE/DATA/Z_clone_candles.yaml')

candle1 = get_candle_0_open_time(file1)
candle2 = get_candle_0_open_time(file2)

if not is_null(candle1) and not is_null(candle2) and candle1 != candle2:
    scripts = [
        'test1.py',
        'test2.py',
        'test3.py',
        'test4.py',
    ]
    for script in scripts:
        script_path = os.path.join(project_root, script)
        if os.path.exists(script_path):
            subprocess.run([sys.executable, script_path], check=True)
        else:
            print(f"Файл {script_path} не найден!")
