import sys
import os
import yaml
sys.dont_write_bytecode = True

# ================= НАСТРОЙКИ ПУТЕЙ =================
TREND_YAML_PATH = 'CORE/DATA/B_trade_config.yaml'
GREEN_SCRIPT_PATH = 'CORE/BACKEND/C_CHECK_TREND/CA_check_green.py'
RED_SCRIPT_PATH = 'CORE/BACKEND/C_CHECK_TREND/CB_check_red.py'
# ===================================================

try:
    with open(TREND_YAML_PATH, encoding='utf-8') as f:
        data = yaml.safe_load(f)
        trend = data.get('TREND', '').strip().upper()
except Exception as e:
    print(f'Ошибка при чтении AB_trade_config.yaml: {e}')
    sys.exit(1)

if trend == 'GREEN':
    script = GREEN_SCRIPT_PATH
elif trend == 'RED':
    script = RED_SCRIPT_PATH
else:
    print(f'Неизвестное значение TREND: {trend}')
    sys.exit(2)

import subprocess

script_path = script
try:
    result = subprocess.run([sys.executable, script_path], check=True)
except Exception as e:
    print(f'Ошибка при запуске {script}: {e}')
    sys.exit(3)
