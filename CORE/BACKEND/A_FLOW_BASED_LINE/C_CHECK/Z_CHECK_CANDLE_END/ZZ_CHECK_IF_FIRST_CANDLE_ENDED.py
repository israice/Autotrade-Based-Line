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

# ============== new ===========
A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "OPEN_TIME"   # field to read from A file
A_CANDLE = 0                # index or CANDLE value (auto-detected)
COMPARISON_OPERATOR = "=="  # Support: '==', '!=', '>', '<', '>=', '<='
Z_CANDLE = 0                # index or CANDLE value (auto-detected)
Z_VALUE_KEY = "OPEN_TIME"   # field to read from Z file
Z_PATH = "CORE/DATA/ZZ_CANDLE.yaml"
# =========================

# Scripts to execute depending on comparison
SCRIPTS_EQUAL: List[str] = [
]
SCRIPTS_NOT_EQUAL: List[str] = [
        "CORE/TOOLS/YY_history_candles/GET_CANDLE_1.py",
]
SCRIPTS_NOT_FOUND: List[str] = [
]

# Child process execution
CHILD_TIMEOUT_SEC = 60       # fail-safe timeout for each script
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


def _case_insensitive_get_from_dict(d: Dict[str, Any], key: str) -> Optional[Any]:
    """Try dict[key], then case-insensitive match over keys."""
    if key in d:
        return d[key]
    if isinstance(key, str):
        kfold = key.casefold()
        for k in d.keys():
            if isinstance(k, str) and k.casefold() == kfold:
                return d[k]
    return None


def mixed_get(container: Any, key: str) -> Optional[Any]:
    """
    Safely get 'key' from possibly mixed YAML structure where levels can be
    dicts or lists-of-dicts. Uses case-insensitive fallback for keys.
    """
    if isinstance(container, dict):
        return _case_insensitive_get_from_dict(container, key)

    if isinstance(container, list):
        # Typical pattern: [{KEY: value}, {OTHER: value2}, ...]
        for item in container:
            if isinstance(item, dict):
                # Direct match
                if key in item:
                    return item[key]
                # Case-insensitive single-key match
                got = _case_insensitive_get_from_dict(item, key)
                if got is not None:
                    return got
        return None

    return None


def as_list(value: Any) -> List[Any]:
    """Normalize any value to a list: list -> same, None -> [], other -> [value]."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def pick_candle_entry(candles: List[Any], candle_id: Any, id_field: str = "CANDLE") -> Optional[Dict[str, Any]]:
    """
    Pick candle dict either by list index (if within range) or by matching id_field == candle_id.
    This makes selection robust to YAML where candles are not strictly positional.
    """
    # 1) Try by positional index
    if isinstance(candle_id, int) and 0 <= candle_id < len(candles):
        entry = candles[candle_id]
        if isinstance(entry, dict):
            return entry

    # 2) Try by field match (id_field equals candle_id)
    for item in candles:
        if isinstance(item, dict) and id_field in item and item[id_field] == candle_id:
            return item

    # 3) As a last resort, if there is exactly one dict, return it
    only_dicts = [x for x in candles if isinstance(x, dict)]
    if len(only_dicts) == 1:
        return only_dicts[0]

    return None


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

    # Accept strings only
    if not isinstance(symbol, str) or not isinstance(timeframe, str):
        return None, None
    return symbol, timeframe


def extract_field_from_candle_file(
    file_path: str,
    symbol: str,
    timeframe: str,
    field_key: str,
    candle_id: Any,
) -> Optional[Any]:
    """
    Traverse the YAML structure:
    BINANCE_FUTURES -> <symbol node> -> <timeframe node> -> candle dict -> field_key

    - Supports either dict or list at each layer.
    - Keys are matched case-insensitively.
    - Candle selection is resilient: first tries index, then matches by CANDLE==candle_id.
    """
    data = load_yaml(file_path)
    if not data:
        return None

    try:
        root = _case_insensitive_get_from_dict(data, YAML_ROOT_KEY) if isinstance(data, dict) else None
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

        candle_entry = pick_candle_entry(candles_list, candle_id, id_field="CANDLE")
        if not isinstance(candle_entry, dict):
            return None

        # Field access with case-insensitive fallback
        value = _case_insensitive_get_from_dict(candle_entry, field_key) if isinstance(candle_entry, dict) else None
        return value
    finally:
        # Explicitly drop large refs and prompt GC
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
    - Inherit parent's stdout/stderr to avoid buffering in memory.
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
