#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Универсальный скрипт для сравнения YAML переменных и запуска скриптов"""

import yaml, subprocess, sys, os

# =============================================================================
# НАСТРОЙКИ
# =============================================================================
FILE_1 = "CORE/DATA/A_candle.yaml"
VARIABLE_NAME = "OPEN_TIME"
COMPARISON_OPERATOR = "=="  # !=, ==, >, <, >=, <=
FILE_2 = "CORE/DATA/Z_candle.yaml"

CANDLE_NOT_ENDED_LIST = [
    "TOOLS/COPY_CANDLES.py",
]

CANDLE_ENDED_LIST = [
    "TOOLS/GET_CANDLE_1_ADD_TO_DBy",
    "TOOLS/COPY_CANDLES.py",
]

STOP_ON_ERROR = True

def load_yaml_var(file, var):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            return None
            
        if isinstance(data, list):
            return data[0].get(var) if data and isinstance(data[0], dict) else None
        elif isinstance(data, dict):
            if var in data:
                return data[var]
            else:
                # assume dict of dicts, get first subdict
                if data:
                    first_key = next(iter(data))
                    return data[first_key].get(var) if isinstance(data[first_key], dict) else None
                return None
        else:
            raise ValueError("Unsupported data type")
    except Exception as e:
        print(f"Ошибка при загрузке {file}: {e}")
        return None

def compare(v1, v2, op):
    ops = {
        "!=": v1 != v2, 
        "==": v1 == v2, 
        ">": v1 > v2, 
        "<": v1 < v2, 
        ">=": v1 >= v2, 
        "<=": v1 <= v2
    }
    return ops.get(op, False)

def run_script(script):
    if not os.path.exists(script):
        print(f"Скрипт не найден: {script}")
        return False
    
    try:
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        print(result.stdout, end='')  # Выводим только stdout скрипта
        if result.stderr:
            print(result.stderr, end='')  # Выводим stderr скрипта, если есть
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка при выполнении {script}: {e}")
        return False

def run_scripts(scripts):
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
        else:
            print(f"Ошибка выполнения: {script}")
            if STOP_ON_ERROR:
                sys.exit(1)
    return success_count == len(scripts)

def main():
    v1 = load_yaml_var(FILE_1, VARIABLE_NAME)
    v2 = load_yaml_var(FILE_2, VARIABLE_NAME)
        
    # ИСПРАВЛЕНИЕ: если значение не найдено, запускаем CANDLE_NOT_ENDED_LIST
    if v1 is None or v2 is None:
        success = run_scripts(CANDLE_NOT_ENDED_LIST)
        sys.exit(0 if success else 1)
    
    # Если оба значения найдены, выполняем сравнение
    comparison_result = compare(v1, v2, COMPARISON_OPERATOR)
    
    if comparison_result:
        success = run_scripts(CANDLE_NOT_ENDED_LIST)
    else:
        print("Условие не выполнено. Запуск CANDLE_ENDED_LIST...")
        success = run_scripts(CANDLE_ENDED_LIST)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
