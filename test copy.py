#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Purpose:
  - Read values from two YAML candle files using symbol/timeframe from BB_USER_SETTINGS.yaml
  - Compare values with a chosen operator
  - Run scripts sequentially depending on the boolean result

Notes:
  - Paths must use forward slashes
  - Settings are at the top; generic logic is at the bottom
  - Comments are in English
"""

# =========================
# ========= SETTINGS ======
# =========================

# Data sources (A and Z)
A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "OPEN_PRICE"          # Field to read from A file
A_CANDLE = 0                        # Candle index to read from A
COMPARISON_OPERATOR = ">=" # one of '==', '!=', '>', '<', '>=', '<='
Z_CANDLE = 0                        # Candle index to read from Z
Z_VALUE_KEY = "OPEN_PRICE"          # Field to read from Z file
Z_PATH = "CORE/DATA/ZZ_CANDLE.yaml"


USER_SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"
SCRIPTS_TRUE = [
    "CORE/TOOLS/msg/ping.py",
]

SCRIPTS_FALSE = [
    "CORE/TOOLS/msg/pong.py",
]

# =========================
# ======== IMPORTS ========
# =========================

import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Union

try:
    import yaml  # Requires PyYAML
except ImportError as e:
    raise SystemExit("PyYAML is required: pip install pyyaml") from e


# =========================
# ======== HELPERS ========
# =========================

JSONLike = Union[Dict[str, Any], List[Any]]


def posix(p: str) -> str:
    """Return the path with forward slashes."""
    return str(Path(p).as_posix())


def load_yaml(path: str) -> JSONLike:
    """Load YAML file safely."""
    path = posix(path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_user_settings(path: str) -> Dict[str, str]:
    """Read SYSTEM_SYMBOL and SYSTEM_TIMEFRAME from settings YAML."""
    data = load_yaml(path)
    if not isinstance(data, dict):
        raise ValueError("BB_USER_SETTINGS.yaml must be a mapping at the top level")

    try:
        symbol = str(data["SYSTEM_SYMBOL"])
        timeframe = str(data["SYSTEM_TIMEFRAME"])
    except KeyError as e:
        raise KeyError(f"Missing required key in settings: {e}") from e

    return {"symbol": symbol, "timeframe": timeframe}


def find_next(container: JSONLike, key: str) -> Any:
    """
    Move one level deeper by 'key'.
    Supports:
      - dict that directly contains 'key'
      - list of single-key dicts where some item contains 'key'
    """
    # Direct dict access
    if isinstance(container, dict):
        if key in container:
            return container[key]

    # List like: [ {key: ...}, {other: ...} ]
    if isinstance(container, list):
        for item in container:
            if isinstance(item, dict) and key in item:
                return item[key]

    raise KeyError(f"Key '{key}' not found in provided structure")


def traverse_chain(root: JSONLike, keys: List[str]) -> Any:
    """Traverse nested structure following keys, supporting dicts or list-of-dicts at each level."""
    node = root
    for k in keys:
        node = find_next(node, k)
    return node


def _flatten_candles_maybe(candles: Any) -> List[Dict[str, Any]]:
    """
    Canonicalize candles collection to a flat list of dicts.
    Handles:
      - list of dicts  -> ok
      - single dict    -> wrap into list
      - nested lists   -> flatten one level
    """
    # Single dict -> list
    if isinstance(candles, dict):
        return [candles]

    # List cases
    if isinstance(candles, list):
        flat: List[Dict[str, Any]] = []
        for item in candles:
            if isinstance(item, dict):
                flat.append(item)
            elif isinstance(item, list):
                # flatten one level
                for sub in item:
                    if isinstance(sub, dict):
                        flat.append(sub)
        if flat:
            return flat



def select_candle(candles: Any, candle_index: int) -> Dict[str, Any]:
    """
    Given the collection of candles, select by:
      1) record where record['CANDLE'] == candle_index, if available
      2) otherwise, by positional index
    """
    flat = _flatten_candles_maybe(candles)

    # Try by 'CANDLE' marker
    for rec in flat:
        if isinstance(rec, dict) and rec.get("CANDLE") == candle_index:
            return rec

    # Fallback by position
    if 0 <= candle_index < len(flat):
        rec = flat[candle_index]
        if isinstance(rec, dict):
            return rec

    raise IndexError(f"Unable to select candle index {candle_index}")


def get_value_from_file(
    data_path: str,
    symbol: str,
    timeframe: str,
    candle_index: int,
    value_key: str,
) -> Any:
    """
    Read YAML -> navigate to BINANCE_FUTURES / symbol / timeframe -> pick candle -> read value_key.
    Supports both mapping and list-of-singleton-dicts nesting styles.
    """
    data = load_yaml(data_path)

    # Navigate: BINANCE_FUTURES -> <symbol> -> <timeframe>
    candles = traverse_chain(data, ["BINANCE_FUTURES", symbol, timeframe])

    # Pick the candle
    candle = select_candle(candles, candle_index)

    # Extract the value
    if value_key not in candle:
        raise KeyError(f"Key '{value_key}' not found in candle record")
    return candle[value_key]


def coerce_for_comparison(a: Any, b: Any, op: str) -> tuple[Any, Any]:
    """
    Coerce values for comparison. For >,<,>=,<= ensure numeric comparison if possible.
    For ==, != allow any types.
    """
    if op in (">", "<", ">=", "<="):
        def to_float(x: Any) -> float:
            if isinstance(x, (int, float)):
                return float(x)
            if isinstance(x, str):
                return float(x.strip())
            raise TypeError(f"Non-numeric value encountered for numeric comparison: {x!r}")

        return to_float(a), to_float(b)
    return a, b


def compare_values(a: Any, b: Any, operator_str: str) -> bool:
    """Compare two values with the specified operator."""
    operators = {
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y,
        ">": lambda x, y: x > y,
        "<": lambda x, y: x < y,
        ">=": lambda x, y: x >= y,
        "<=": lambda x, y: x <= y,
    }

    if operator_str not in operators:
        raise ValueError(f"Unsupported operator '{operator_str}'. Use one of {list(operators)}")

    a_c, b_c = coerce_for_comparison(a, b, operator_str)
    return operators[operator_str](a_c, b_c)


def run_scripts_sequentially(scripts: List[str]) -> None:
    """
    Run each script using the current Python interpreter.
    Stops on the first failure (non-zero exit code).
    """
    for script in scripts:
        script_path = posix(script)
        cmd = [sys.executable, script_path]
        completed = subprocess.run(cmd, check=False)
        if completed.returncode != 0:
            raise SystemExit(f"Script failed with exit code {completed.returncode}: {script_path}")


# =========================
# ========= LOGIC =========
# =========================

def main() -> None:
    # Read user settings (symbol, timeframe)
    settings = read_user_settings(USER_SETTINGS_PATH)
    symbol = settings["symbol"]
    timeframe = settings["timeframe"]

    # Read values from A and Z
    a_value = get_value_from_file(
        data_path=A_PATH,
        symbol=symbol,
        timeframe=timeframe,
        candle_index=A_CANDLE,
        value_key=A_VALUE_KEY,
    )

    z_value = get_value_from_file(
        data_path=Z_PATH,
        symbol=symbol,
        timeframe=timeframe,
        candle_index=Z_CANDLE,
        value_key=Z_VALUE_KEY,
    )

    # Compare
    result = compare_values(a_value, z_value, COMPARISON_OPERATOR)

    # Run scripts based on result
    scripts_to_run = SCRIPTS_TRUE if result else SCRIPTS_FALSE
    run_scripts_sequentially(scripts_to_run)


if __name__ == "__main__":
    main()
