#!/usr/bin/env python3
import yaml
import subprocess
import sys

# Настройки
CONFIG_FILE = "CORE/DATA/triggers_config.yaml"
PERCENT_STATUS_KEY = "PERCENT_STATUS"

GREEN_LIST = [
    "CORE/BACKEND/D_CHECK_PERCENT_SELL/DAA_check_LONG_SELL_percent.py",
]

RED_LIST = [
    "CORE/BACKEND/D_CHECK_PERCENT_SELL/DAB_check_SHORT_SELL_percent.py",
]

# Основная логика
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

percent_status = float(config[PERCENT_STATUS_KEY])

if percent_status > 0:
    script_list = GREEN_LIST
elif percent_status < 0:
    script_list = RED_LIST
else:
    sys.exit(0)

for script in script_list:
    subprocess.run([sys.executable, script], check=True)