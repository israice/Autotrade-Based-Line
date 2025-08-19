#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Any, Dict, Optional, Tuple, List
from ruamel.yaml import YAML

# =========================
# ====== SETTINGS =========
# =========================

# Files
SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"   # expects SYSTEM_SYMBOL, SYSTEM_TIMEFRAME
YAML_ROOT_KEY = "BINANCE_FUTURES"

INPUT_FILE = "CORE/DATA/AA_CANDLE.yaml"
OUTPUT_FILE = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"
OUTPUT_DIR = "CORE/BACKEND/B_CREATE_DATA"

# Fields
OPEN_KEY = "OPEN_PRICE"
CLOSE_KEY = "CLOSE_PRICE"
PERCENT_KEY = "PERCENT_STATUS"

# Candle selection rule:
# 0 -> find candle where CANDLE == 0 (fallback to first element)
# >=1 -> 1-based positional index (1 -> first element)
CANDLE_INDEX = 0

# Rounding
ROUND_DIGITS = 3

# =========================
# ========= LOGIC =========
# =========================

yaml = YAML()
yaml.preserve_quotes = True  # keep original quoting where possible


def load_yaml(path: str) -> Optional[Dict[str, Any]]:
    """Load YAML and return dict or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_yaml(path: str, data: Dict[str, Any]) -> None:
    """Save YAML preserving style."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def find_key(container: Any, key: str) -> Optional[Any]:
    """Fetch value by key from dict or from first dict inside a list."""
    if isinstance(container, dict):
        return container.get(key)
    if isinstance(container, list):
        for item in container:
            if isinstance(item, dict) and key in item:
                return item[key]
    return None


def pick_candle(candles: List[Any], candle_no: int) -> Optional[Dict[str, Any]]:
    """
    Pick candle by rule:
    - 0 -> entry whose CANDLE == 0 (fallback to first element)
    - >=1 -> 1-based positional index
    """
    only_dicts = [c for c in candles if isinstance(c, dict)]
    if not only_dicts:
        return None
    if candle_no == 0:
        for c in only_dicts:
            try:
                if int(str(c.get("CANDLE")).strip()) == 0:
                    return c
            except Exception:
                pass
        return only_dicts[0]
    idx = candle_no - 1
    return only_dicts[idx] if 0 <= idx < len(only_dicts) else None


def read_settings(path: str) -> Tuple[Optional[str], Optional[str]]:
    """Read SYSTEM_SYMBOL and SYSTEM_TIMEFRAME."""
    s = load_yaml(path)
    if not s:
        return None, None
    sym = s.get("SYSTEM_SYMBOL")
    tf = s.get("SYSTEM_TIMEFRAME")
    return (sym, tf) if isinstance(sym, str) and isinstance(tf, str) else (None, None)


def get_open_close(
    file_path: str, symbol: str, timeframe: str, candle_no: int
) -> Tuple[Optional[float], Optional[float]]:
    """Extract OPEN/CLOSE from the selected candle according to rules."""
    data = load_yaml(file_path)
    if not data:
        return None, None

    root = data.get(YAML_ROOT_KEY)
    if root is None:
        return None, None

    sym_node = find_key(root, symbol)
    tf_node = find_key(sym_node, timeframe) if sym_node is not None else None
    if tf_node is None:
        return None, None

    candles = tf_node if isinstance(tf_node, list) else [tf_node]
    entry = pick_candle(candles, int(candle_no))
    if not isinstance(entry, dict):
        return None, None

    try:
        return float(entry[OPEN_KEY]), float(entry[CLOSE_KEY])
    except Exception:
        return None, None


def main() -> None:
    # Settings → symbol/timeframe
    symbol, timeframe = read_settings(SETTINGS_PATH)
    if not symbol or not timeframe:
        raise RuntimeError("SYSTEM_SYMBOL or SYSTEM_TIMEFRAME not found in settings.")

    # Read candle values
    open_val, close_val = get_open_close(INPUT_FILE, symbol, timeframe, CANDLE_INDEX)
    if open_val is None or close_val is None:
        raise ValueError(f"Failed to read '{OPEN_KEY}'/'{CLOSE_KEY}' from {INPUT_FILE}.")

    # Calculate % change
    if close_val == open_val:
        print("Close price equals open price, no percentage change.")
        sys.exit(0)
    percent = round(((close_val - open_val) / open_val) * 100.0, ROUND_DIGITS)

    # Ensure output dir and load existing config
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = load_yaml(OUTPUT_FILE) or {}

    # Update and save
    out[PERCENT_KEY] = percent
    save_yaml(OUTPUT_FILE, out)

    # Quiet by default; uncomment if needed
    # print(f"{PERCENT_KEY}: {percent} %")


if __name__ == "__main__":
    main()
