#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import gc
import subprocess
from typing import Any, Dict, Optional, Tuple, List

SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"  # contains SYSTEM_SYMBOL, SYSTEM_TIMEFRAME
YAML_ROOT_KEY = "BINANCE_FUTURES"
# Candle files
A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "OPEN_TIME"  # field to read from A file
A_CANDLE = 0
COMPARISON_OPERATOR = "=="  # Support: '==', '!=', '>', '<', '>=', '<='
Z_CANDLE = 0
Z_VALUE_KEY = "OPEN_TIME"  # field to read from Z file
Z_PATH = "CORE/DATA/ZZ_CANDLE.yaml"

SCRIPTS_EQUAL: List[str] = [
    "CORE/TOOLS/msg/pong.py",
    "CORE/TOOLS/ZZ_candle/COPY_AA_TO_ZZ.py",
]
SCRIPTS_NOT_EQUAL: List[str] = [
    "CORE/TOOLS/msg/pong.py",
    "CORE/TOOLS/YY_history_candles/get_CANDLE_1_ADD_TO_DB.py",
    "CORE/TOOLS/ZZ_candle/COPY_AA_TO_ZZ.py",
]
SCRIPTS_NOT_FOUND: List[str] = [
    "CORE/TOOLS/msg/pong.py",
    "CORE/TOOLS/ZZ_candle/COPY_AA_TO_ZZ.py",
]

# Child process execution
CHILD_TIMEOUT_SEC = 60  # fail-safe timeout for each script (tune as needed)
PYTHON_BIN = sys.executable  # interpreter used for child scripts

# =========================
# ====== LOGIC ============
# =========================

def load_yaml(path: str) -> Optional[Dict[str, Any]]:
    """Load YAML and return dict or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def mixed_get(container: Any, key: str) -> Optional[Any]:
    """
    Safely get 'key' from possibly mixed YAML structure where levels can be
    dicts or lists of dicts.
    """
    if isinstance(container, dict):
        return container.get(key)
    if isinstance(container, list):
        for item in container:
            if isinstance(item, dict) and key in item:
                return item[key]
    return None


def as_list(value: Any) -> list:
    """Normalize any value to a list: list -> same, None -> [], other -> [value]."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_system_settings(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Read SYSTEM_SYMBOL and SYSTEM_TIMEFRAME from BB_USER_SETTINGS.yaml.
    Returns (symbol, timeframe).
    """
    data = load_yaml(path)
    if not data:
        return None, None

    symbol = data.get("SYSTEM_SYMBOL")
    timeframe = data.get("SYSTEM_TIMEFRAME")
    if not isinstance(symbol, str) or not isinstance(timeframe, str):
        return None, None
    return symbol, timeframe


def extract_field_from_candle_file(
    file_path: str,
    symbol: str,
    timeframe: str,
    field_key: str,
    candle_index: int,
) -> Optional[Any]:
    """
    Traverse the YAML structure:
    BINANCE_FUTURES -> <list or dict with symbol> -> <list or dict with timeframe> -> [candle_index] -> field_key
    Returns the field value or None if anything is missing.
    """
    data = load_yaml(file_path)
    if not data:
        return None

    try:
        root = data.get(YAML_ROOT_KEY)
        if root is None:
            return None

        symbol_node = mixed_get(root, symbol)
        if symbol_node is None:
            return None

        timeframe_node = mixed_get(symbol_node, timeframe)
        if timeframe_node is None:
            return None

        candles_list = as_list(timeframe_node)
        if not candles_list or not (0 <= candle_index < len(candles_list)):
            return None

        candle_entry = candles_list[candle_index]
        if not isinstance(candle_entry, dict):
            return None

        return candle_entry.get(field_key)
    finally:
        # Explicitly drop large refs and prompt GC to minimize RSS between loop calls
        del data
        gc.collect()


def compare_values(a: Any, b: Any, op: str) -> bool:
    """Compare two values with the given operator."""
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    if op == ">":
        return a > b
    if op == "<":
        return a < b
    if op == ">=":
        return a >= b
    if op == "<=":
        return a <= b
    raise ValueError(f"Unsupported comparison operator: {op}")


def execute_scripts(scripts: List[str]) -> None:
    """
    Execute python files in the given order in isolated subprocesses.
    - No in-memory buffering of output (inherits parent's stdout/stderr).
    - Timeout per script to prevent hangs.
    - No exec() inside current interpreter -> no module cache growth.
    """
    if not scripts:
        return

    for script_path in scripts:
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}", flush=True)
            continue

        try:
            # Inherit stdout/stderr to avoid buffering in memory
            subprocess.run(
                [PYTHON_BIN, "-u", script_path],
                check=False,
                timeout=CHILD_TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired:
            print(f"Script timed out: {script_path}", flush=True)
        except Exception as exc:
            print(f"Error while executing {script_path}: {exc}", flush=True)


def main() -> None:
    # 1) Load system symbol/timeframe
    symbol, timeframe = load_system_settings(SETTINGS_PATH)

    # If settings missing, we cannot proceed reliably
    if not symbol or not timeframe:
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 2) Extract values from A and Z files
    a_value = extract_field_from_candle_file(
        A_PATH, symbol, timeframe, A_VALUE_KEY, A_CANDLE
    )
    z_value = extract_field_from_candle_file(
        Z_PATH, symbol, timeframe, Z_VALUE_KEY, Z_CANDLE
    )

    # 3) Decide what to run
    if a_value is None or z_value is None:
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 4) Compare according to operator
    try:
        condition = compare_values(a_value, z_value, COMPARISON_OPERATOR)
    except Exception as exc:
        print(f"Comparison error: {exc}", flush=True)
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 5) Run scripts accordingly (no duplication filtering by design)
    if condition:
        execute_scripts(SCRIPTS_EQUAL)
    else:
        execute_scripts(SCRIPTS_NOT_EQUAL)

    # Encourage prompt GC between looped invocations by parent
    gc.collect()


if __name__ == "__main__":
    main()
