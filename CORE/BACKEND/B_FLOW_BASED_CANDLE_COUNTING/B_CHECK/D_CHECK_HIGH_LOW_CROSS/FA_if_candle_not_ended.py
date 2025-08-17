#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный скрипт для сравнения YAML переменных и запуска скриптов"""

import yaml, subprocess, sys, os

# =============================================================================
# НАСТРОЙКИ
# =============================================================================
FILE_1 = "CORE/DATA/AA_CANDLE.yaml"
VARIABLE_NAME = "candle_0_open"
COMPARISON_OPERATOR = "=="  # !=, ==, >, <, >=, <=
FILE_2 = "CORE/DATA/ZZ_CANDLE.yaml"

SCRIPTS = [
    "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FAA_check_green_or_red.py",
]
STOP_ON_ERROR = True

def load_yaml_var(file, var):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data[0][var] if isinstance(data, list) else data[var]
    except Exception:
        return None

def compare(v1, v2, op):
    ops = {"!=": v1 != v2, "==": v1 == v2, ">": v1 > v2, "<": v1 < v2, ">=": v1 >= v2, "<=": v1 <= v2}
    return ops.get(op, False)

def run_script(script):
    if not os.path.exists(script):
        return False
    
    try:
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        print(result.stdout, end='')  # Выводим только stdout скрипта
        if result.stderr:
            print(result.stderr, end='')  # Выводим stderr скрипта, если есть
        return result.returncode == 0
    except Exception:
        return False

def main():
    v1 = load_yaml_var(FILE_1, VARIABLE_NAME)
    v2 = load_yaml_var(FILE_2, VARIABLE_NAME)
    
    if v1 is None or v2 is None:
        sys.exit(1)
    
    comparison_result = compare(v1, v2, COMPARISON_OPERATOR)
    
    if comparison_result:
        success_count = 0
        for script in SCRIPTS:
            if run_script(script):
                success_count += 1
            else:
                if STOP_ON_ERROR:
                    sys.exit(1)
        sys.exit(0 if success_count == len(SCRIPTS) else 1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()