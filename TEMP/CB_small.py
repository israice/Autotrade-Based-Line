import sys
import os
import yaml
import subprocess
sys.dont_write_bytecode = True

# ==== НАСТРОЙКИ ====
PROJECT_ROOT_LEVELS_UP = 3
YAML_REL_PATH = 'CORE/DATA/A_small_new_candles_data.yaml'
CANDLE_0_OPEN_KEY = 'candle_0_open'
CANDLE_1_OPEN_KEY = 'candle_1_open'
YAML_ENCODING = 'utf-8'
SCRIPT_LONG = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/CAA_SELL_LONG.py',
    'CORE/BACKEND/C_CHECK_CANDLE_END/CAAB_reset_CANDLE_PERCENT_NEXT.py',
    ]
SCRIPT_SHORT = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/CAB_SELL_SHORT.py',
    'CORE/BACKEND/C_CHECK_CANDLE_END/CABB_reset_CANDLE_PERCENT_NEXT.py',
    ]

# ==== ОСНОВНОЙ КОД ====
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * PROJECT_ROOT_LEVELS_UP)))
yaml_path = os.path.join(project_root, YAML_REL_PATH)
with open(yaml_path, encoding=YAML_ENCODING) as f:
    data = yaml.safe_load(f)

candle_0_open = float(data[0][CANDLE_0_OPEN_KEY])
candle_1_open = float(data[1][CANDLE_1_OPEN_KEY])

if candle_0_open > candle_1_open:
    scripts = [SCRIPT_LONG]
elif candle_0_open < candle_1_open:
    scripts = [SCRIPT_SHORT]
else:
    scripts = [SCRIPT_LONG, SCRIPT_SHORT]

for script in scripts:
    script_path = os.path.join(project_root, script)
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break
