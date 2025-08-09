#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Universal script for comparing YAML variables and running scripts"""

import yaml
import subprocess
import sys
import os

# =============================================================================
# SETTINGS
# =============================================================================
FILE_1 = "CORE/DATA/A_candle.yaml"
VARIABLE_NAME = "candle_0_open"
FILE_2 = "CORE/DATA/Z_candle.yaml"

SCRIPTS_GREEN = [
    "CORE/BACKEND/Z_TOOLS/reset_COUNTER_OPEN_LINE_in_triggers_config.py",
    "CORE/BACKEND/Z_TOOLS/message_ping.py",
]
SCRIPTS_RED = [
    "CORE/BACKEND/Z_TOOLS/reset_COUNTER_OPEN_LINE_in_triggers_config.py",
    "CORE/BACKEND/Z_TOOLS/message_pong.py",
]

STOP_ON_ERROR = True


def load_yaml_var(file, var):
    """Load specific variable from YAML file"""
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data[0][var] if isinstance(data, list) else data[var]
    except:
        return None


def run_script(script):
    """Run a Python script and return True if it exits with code 0"""
    if not os.path.exists(script):
        return False
    try:
        result = subprocess.run([sys.executable, script])
        return result.returncode == 0
    except:
        return False


def execute_scripts(script_list):
    """Run all scripts in given list"""
    success_count = 0
    for script in script_list:
        if run_script(script):
            success_count += 1
        elif STOP_ON_ERROR:
            sys.exit(1)
    sys.exit(0 if success_count == len(script_list) else 1)


def main():
    v1 = load_yaml_var(FILE_1, VARIABLE_NAME)
    v2 = load_yaml_var(FILE_2, VARIABLE_NAME)

    if v1 is None or v2 is None:
        sys.exit(1)

    if v1 > v2:
        execute_scripts(SCRIPTS_GREEN)
    elif v1 < v2:
        execute_scripts(SCRIPTS_RED)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
