import sys
import os
import yaml
sys.dont_write_bytecode = True

# ================= НАСТРОЙКИ ПУТЕЙ =================
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
TREND_YAML_PATH = os.path.join(project_root, 'CORE/DATA/B_trade_config.yaml')
GREEN_SCRIPT_PATH = os.path.join(project_root, 'CORE/BACKEND/C_CHECK_TREND/CA_check_green.py')
RED_SCRIPT_PATH = os.path.join(project_root, 'CORE/BACKEND/C_CHECK_TREND/CB_check_red.py')
# ===================================================

try:
    with open(TREND_YAML_PATH, encoding='utf-8') as f:
        data = yaml.safe_load(f)
        trend = data.get('TREND', '').strip().upper()
except Exception as e:
    print(f'Ошибка при чтении AB_trade_config.yaml: {e}')
    sys.exit(1)

if trend == 'GREEN':
    script_path = GREEN_SCRIPT_PATH
elif trend == 'RED':
    script_path = RED_SCRIPT_PATH
else:
    print(f'Неизвестное значение TREND: {trend}')
    sys.exit(2)

import subprocess

try:
    result = subprocess.run([sys.executable, script_path], check=True)
except Exception as e:
    print(f'Ошибка при запуске {script_path}: {e}')
    sys.exit(3)
