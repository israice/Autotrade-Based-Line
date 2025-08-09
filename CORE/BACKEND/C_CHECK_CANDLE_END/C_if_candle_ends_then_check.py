#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный скрипт для сравнения YAML переменных и запуска скриптов"""

import yaml, subprocess, sys, os
from datetime import datetime

# =============================================================================
# НАСТРОЙКИ
# =============================================================================
FILE_1 = "CORE/DATA/A_candle.yaml"
VARIABLE_NAME = "candle_0_open_time"
COMPARISON_OPERATOR = "!="  # !=, ==, >, <, >=, <=
FILE_2 = "CORE/DATA/Z_candle.yaml"

SCRIPTS = [
    "CORE/BACKEND/C_CHECK_CANDLE_END/CA_check_trend.py",
]
VERBOSE = True
STOP_ON_ERROR = True

def load_yaml_var(file, var):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data[0][var] if isinstance(data, list) else data[var]
    except:
        return None

def compare(v1, v2, op):
    ops = {"!=": v1 != v2, "==": v1 == v2, ">": v1 > v2, "<": v1 < v2, ">=": v1 >= v2, "<=": v1 <= v2}
    return ops.get(op, False)

def run_script(script):
    if not os.path.exists(script):
        return False
    
    try:
        # Вывод только от запускаемых скриптов без перехвата
        result = subprocess.run([sys.executable, script])
        return result.returncode == 0
    except:
        return False

def main():
    v1, v2 = load_yaml_var(FILE_1, VARIABLE_NAME), load_yaml_var(FILE_2, VARIABLE_NAME)
    
    if v1 is None or v2 is None:
        sys.exit(1)
    
    if compare(v1, v2, COMPARISON_OPERATOR):
        success_count = 0
        
        for script in SCRIPTS:
            if run_script(script):
                success_count += 1
            elif STOP_ON_ERROR:
                sys.exit(1)
        
        sys.exit(0 if success_count == len(SCRIPTS) else 1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()