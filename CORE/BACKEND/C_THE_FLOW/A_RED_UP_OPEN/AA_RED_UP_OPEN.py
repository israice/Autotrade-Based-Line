#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import gc
import subprocess
from typing import Any, Dict, Optional, Tuple, List, Union

# =========================
# ====== SETTINGS =========
# =========================

SETTINGS_PATH = "settings.yaml"   # may contain SYSTEM_SYMBOL and SYSTEM_TIMEFRAME in any casing/level
YAML_ROOT_KEY = "BINANCE_FUTURES"

# ===== Cross-file field comparisons (A vs Z) =====
A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "CLOSE_PRICE"          # field to read from A file
A_CANDLE: Union[int, str] = 0        # значение поля CANDLE для поиска (тип не важен: 1 == "1")
COMPARISON_OPERATOR = ">"            # one of: '==', '!=', '>', '<', '>=', '<='
Z_CANDLE: Union[int, str] = 1        # значение поля CANDLE для поиска (тип не важен: 1 == "1")
Z_VALUE_KEY = "OPEN_PRICE"           # field to read from Z file
Z_PATH = "CORE/DATA/YY_HISTORY_CANDLES.yaml"

# ===== Scripts to execute depending on comparison result =====
SCRIPTS_EQUAL: List[str] = [
    "CORE/TOOLS/msg_RED_UP_OPEN.py", 
    "CORE/TOOLS/DISABLE_RED_UP_OPEN.py",
    "CORE/TOOLS/ENABLE_RED_DOWN_OPEN.py",
    # ############
    "CORE/TOOLS/DISABLE_GREEN_UP_HIGH.py",
    "CORE/TOOLS/ENABLE_RED_DOWN_LOW.py",
    # ###############################
    "CORE/TOOLS/COPY_ORDER_ACCOUNT_ID.py",
    "CORE/TOOLS/COPY_ORDER_SYMBOL.py",
    "CORE/TOOLS/COPY_ORDER_QUANTITY.py",
    # ############
    "CORE/TOOLS/COPY_ORDER_SIDE_BUY.py",
    "CORE/TOOLS/COPY_ORDER_POSITION_SIDE_LONG.py",
    "CORE/TOOLS/COPY_ORDER_TYPE_MARKET.py",
    # ############
    # "CORE/TOOLS/ORDER_BUY_LONG.py",
    # "CORE/TOOLS/ORDER_SELL_SHORT.py",
    # ###############################
]
SCRIPTS_NOT_EQUAL: List[str] = [

]
SCRIPTS_NOT_FOUND: List[str] = [
    # e.g. "CORE/BACKEND/on_not_found.py",
]

# ===== Child process execution =====
CHILD_TIMEOUT_SEC = 60       # per script timeout
PYTHON_BIN = sys.executable  # python interpreter for child scripts

# =========================
# ========= LOGIC =========
# =========================

def load_yaml(path: str) -> Optional[Any]:
    """Load YAML file and return parsed object or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _ci_key_get(d: Dict[str, Any], key: str) -> Optional[Any]:
    """Case-insensitive dict key access."""
    if not isinstance(d, dict):
        return None
    if key in d:
        return d[key]
    if isinstance(key, str):
        kfold = key.casefold()
        for k, v in d.items():
            if isinstance(k, str) and k.casefold() == kfold:
                return v
    return None


def deep_find_ci(container: Any, key: str) -> Optional[Any]:
    """
    Recursively search for a (case-insensitive) key anywhere in a nested dict/list structure.
    Returns the first match found (DFS).
    """
    if isinstance(container, dict):
        got = _ci_key_get(container, key)
        if got is not None:
            return got
        for v in container.values():
            found = deep_find_ci(v, key)
            if found is not None:
                return found
        return None
    if isinstance(container, list):
        for item in container:
            found = deep_find_ci(item, key)
            if found is not None:
                return found
        return None
    return None


def mixed_get(container: Any, key: str) -> Optional[Any]:
    """
    Get 'key' from a structure where each level can be dict or list-of-dicts.
    Keys are matched case-insensitively.
    """
    if isinstance(container, dict):
        return _ci_key_get(container, key)

    if isinstance(container, list):
        # Expect a list of dicts like: [{KEY: value}, {OTHER: value2}, ...]
        for item in container:
            if isinstance(item, dict):
                if key in item:
                    return item[key]
                got = _ci_key_get(item, key)
                if got is not None:
                    return got
        return None

    return None


def as_list(value: Any) -> List[Any]:
    """Normalize any value to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_scalar(x: Any) -> Any:
    """
    Normalize scalars for loose equality:
    - strip strings, try int, then float
    - keep bool as-is
    """
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        # try int
        try:
            return int(s)
        except Exception:
            pass
        # try float
        try:
            return float(s)
        except Exception:
            pass
        return s
    return x


def pick_candle_entry(candles: List[Any], candle_id: Any, id_field: str = "CANDLE") -> Optional[Dict[str, Any]]:
    """
    Select a candle entry STRICTLY by matching the field (id_field == candle_id).
    Позиционный индекс НЕ используется.
    Также поддерживает случай, когда в списке ровно один словарь.
    Сопоставление идентификатора «мягкое»: 1 == "1".
    """
    target = _normalize_scalar(candle_id)

    # Ищем по полю id_field (без учета регистра ключа)
    for item in candles:
        if isinstance(item, dict):
            v = _ci_key_get(item, id_field)
            if v is not None and _normalize_scalar(v) == target:
                return item

    # Если в списке ровно один словарь — используем его
    only_dicts = [x for x in candles if isinstance(x, dict)]
    if len(only_dicts) == 1:
        return only_dicts[0]

    return None


def load_system_settings(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Load SYSTEM_SYMBOL and SYSTEM_TIMEFRAME from settings file.
    - Case-insensitive keys
    - Can be nested anywhere in the YAML
    Returns (symbol, timeframe) or (None, None) on failure.
    """
    data = load_yaml(path)
    if data is None:
        return None, None

    symbol = deep_find_ci(data, "SYSTEM_SYMBOL")
    timeframe = deep_find_ci(data, "SYSTEM_TIMEFRAME")

    # Accept only strings
    if isinstance(symbol, str) and isinstance(timeframe, str):
        symbol = symbol.strip()
        timeframe = timeframe.strip()
        return (symbol if symbol else None, timeframe if timeframe else None)

    return None, None


def extract_field_from_candle_file(
    file_path: str,
    symbol: str,
    timeframe: str,
    field_key: str,
    candle_id: Any,
) -> Optional[Any]:
    """
    Navigate:
      BINANCE_FUTURES -> <symbol> -> <timeframe> -> [list of candle entries] -> entry with CANDLE == candle_id -> field_key
    Each layer can be a dict or a list-of-dicts.
    """
    data = load_yaml(file_path)
    if data is None:
        return None

    try:
        root = _ci_key_get(data, YAML_ROOT_KEY) if isinstance(data, dict) else None
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

        value = _ci_key_get(candle_entry, field_key)
        return value
    finally:
        del data
        gc.collect()


def _to_number_if_possible(x: Any) -> Any:
    """Try to coerce to int/float for numeric comparisons; otherwise return as-is."""
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip()
        try:
            return int(s)
        except Exception:
            pass
        try:
            return float(s)
        except Exception:
            pass
    return x


def compare_values(a: Any, b: Any, op: str) -> bool:
    """
    Compare two values with the given operator.
    Пытаемся привести к числам для корректного сравнения, иначе сравнение оригиналов.
    """
    a2 = _to_number_if_possible(a)
    b2 = _to_number_if_possible(b)

    if op == "==":
        return a2 == b2
    if op == "!=":
        return a2 != b2
    if op == ">":
        return a2 > b2
    if op == "<":
        return a2 < b2
    if op == ">=":
        return a2 >= b2
    if op == "<=":
        return a2 <= b2
    raise ValueError(f"Unsupported comparison operator: {op}")


def execute_scripts(scripts: List[str]) -> None:
    """Run scripts sequentially in subprocesses with a timeout."""
    if not scripts:
        return

    for script_path in scripts:
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}", flush=True)
            continue
        try:
            subprocess.run([PYTHON_BIN, "-u", script_path], check=False, timeout=CHILD_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            print(f"Script timed out: {script_path}", flush=True)
        except Exception as exc:
            print(f"Error while executing {script_path}: {exc}", flush=True)


def main() -> None:
    # 1) Load system symbol/timeframe (case-insensitive, nested-safe)
    symbol, timeframe = load_system_settings(SETTINGS_PATH)

    if not symbol or not timeframe:
        execute_scripts(SCRIPTS_NOT_FOUND)
        return

    # 2) Extract values from A and Z files (по CANDLE, не по индексу)
    a_value = extract_field_from_candle_file(A_PATH, symbol, timeframe, A_VALUE_KEY, A_CANDLE)
    z_value = extract_field_from_candle_file(Z_PATH, symbol, timeframe, Z_VALUE_KEY, Z_CANDLE)

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
