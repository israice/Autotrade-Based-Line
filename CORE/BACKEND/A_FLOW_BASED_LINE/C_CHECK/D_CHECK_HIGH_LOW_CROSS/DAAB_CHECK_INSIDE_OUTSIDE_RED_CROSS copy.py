#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import gc
import subprocess
from typing import Any, Dict, Optional, Tuple, List

# =========================
# ====== SETTINGS =========
# =========================

SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"  # contains SYSTEM_SYMBOL, SYSTEM_TIMEFRAME
YAML_ROOT_KEY = "BINANCE_FUTURES"

# Candle sources and fields
A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "CLOSE_PRICE"   # field to read from A file
A_CANDLE = 0                 # candle index: 0 -> candle with CANDLE: 0; 1+ -> 1-based position
COMPARISON_OPERATOR = ">"    # Supported: '==', '!=', '>', '<', '>=', '<='
Z_PATH = "CORE/DATA/YY_HISTORY_CANDLES.yaml"
Z_VALUE_KEY = "LOW_PRICE"   # field to read from Z file
Z_CANDLE = 1                 # candle index: 0 -> candle with CANDLE: 0; 1+ -> 1-based position

# Comparison

# Script lists
SCRIPTS_EQUAL: List[str] = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/C_CHECK/D_CHECK_HIGH_LOW_CROSS/DAABA_CHECK_STATUS_CROSSING_UP_RED.py",
    
]
SCRIPTS_NOT_EQUAL: List[str] = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/C_CHECK/D_CHECK_HIGH_LOW_CROSS/DAABB_CHECK_STATUS_CROSSING_DOWN_RED.py",
]
SCRIPTS_NOT_FOUND: List[str] = [
]

# Child process execution
CHILD_TIMEOUT_SEC = 60
PYTHON_BIN = sys.executable


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
    Safely get 'key' from possibly mixed YAML structure (dict or list of dicts).
    Note: there is no candle-list iteration here; only shallow access for symbol/timeframe.
    """
    if isinstance(container, dict):
        return container.get(key)
    if isinstance(container, list):
        # Access first matching dict that contains the key (minimal scan at this level only)
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
    """Read SYSTEM_SYMBOL and SYSTEM_TIMEFRAME from BB_USER_SETTINGS.yaml."""
    data = load_yaml(path)
    if not data:
        return None, None

    symbol = data.get("SYSTEM_SYMBOL")
    timeframe = data.get("SYSTEM_TIMEFRAME")
    if not isinstance(symbol, str) or not isinstance(timeframe, str):
        return None, None
    return symbol, timeframe


def _to_int_safe(x: Any) -> Optional[int]:
    """Try to convert value to int; return None on failure."""
    try:
        return int(str(x).strip())
    except Exception:
        return None


def _pick_candle_entry(candles_list: List[Any], candle_no: int) -> Optional[Dict[str, Any]]:
    """
    Select candle entry by rule:
    - candle_no == 0  -> find entry where CANDLE == 0 (by field value). If not found, fallback to first element.
    - candle_no >= 1  -> treat as 1-based positional index (1 -> first, 2 -> second, ...).
    """
    if not candles_list:
        return None

    # Ensure elements are dicts
    norm_list = [c for c in candles_list if isinstance(c, dict)]
    if not norm_list:
        return None

    if candle_no == 0:
        # Search by label field CANDLE == 0
        for c in norm_list:
            lbl = _to_int_safe(c.get("CANDLE"))
            if lbl == 0:
                return c
        # Fallback: assume most-recent first ordering
        return norm_list[0]

    # 1-based positional access
    idx = candle_no - 1
    if 0 <= idx < len(norm_list):
        return norm_list[idx]
    return None


def extract_field_from_candle_file(
    file_path: str,
    symbol: str,
    timeframe: str,
    field_key: str,
    candle_no: int,
) -> Optional[Any]:
    """
    Access candle field by index:
    - candle_no == 0  -> pick candle with CANDLE: 0 (or fallback to first element).
    - candle_no >= 1  -> 1-based positional index into the list.
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
        if not candles_list:
            return None

        candle_entry = _pick_candle_entry(candles_list, int(candle_no))
        if not isinstance(candle_entry, dict):
            return None

        return candle_entry.get(field_key)
    finally:
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
    """
    if not scripts:
        return

    for script_path in scripts:
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}", flush=True)
            continue

        try:
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

    if not symbol or not timeframe:
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 2) Candle access by rule (0 -> CANDLE:0, >=1 -> 1-based index)
    a_value = extract_field_from_candle_file(
        A_PATH, symbol, timeframe, A_VALUE_KEY, A_CANDLE
    )
    z_value = extract_field_from_candle_file(
        Z_PATH, symbol, timeframe, Z_VALUE_KEY, Z_CANDLE
    )

    if a_value is None or z_value is None:
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 3) Compare and branch
    try:
        condition = compare_values(a_value, z_value, COMPARISON_OPERATOR)
    except Exception as exc:
        print(f"Comparison error: {exc}", flush=True)
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    if condition:
        execute_scripts(SCRIPTS_EQUAL)
    else:
        execute_scripts(SCRIPTS_NOT_EQUAL)

    gc.collect()


if __name__ == "__main__":
    main()
