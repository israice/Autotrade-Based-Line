import sys
import os
import yaml
sys.dont_write_bytecode = True

# Путь к yaml-файлу с трендом
trend_yaml = os.path.join(os.path.dirname(__file__), 'AB_check_trend.yaml')

try:
    with open(trend_yaml, encoding='utf-8') as f:
        data = yaml.safe_load(f)
        trend = data.get('TREND', '').strip().upper()
except Exception as e:
    print(f'Ошибка при чтении AB_check_trend.yaml: {e}')
    sys.exit(1)

if trend == 'GREEN':
    script = 'ACA_check_green.py'
elif trend == 'RED':
    script = 'ACB_check_red.py'
else:
    print(f'Неизвестное значение TREND: {trend}')
    sys.exit(2)

import subprocess

script_path = os.path.join(os.path.dirname(__file__), script)
try:
    result = subprocess.run([sys.executable, script_path], check=True)
except Exception as e:
    print(f'Ошибка при запуске {script}: {e}')
    sys.exit(3)
