#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================
# ========= SETTINGS ======
# =========================
USER_SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"

A_PATH = "CORE/DATA/AA_CANDLE.yaml"
A_VALUE_KEY = "OPEN_PRICE"
A_CANDLE = 0
COMPARISON_OPERATOR = ">"
Z_CANDLE = 0
Z_VALUE_KEY = "OPEN_PRICE"
Z_PATH = "CORE/DATA/ZZ_CANDLE.yaml"

SCRIPTS_TRUE = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/D_RUNNERS/AA_END_GREEN.py",
]

SCRIPTS_FALSE = [
    "CORE/BACKEND/A_FLOW_BASED_LINE/D_RUNNERS/AB_END_RED.py",
]

# =========================
# ========= LOGIC =========
# =========================

# Comments are in English; values are read as strings; paths use forward slashes.

import sys
import subprocess
from pathlib import Path
import yaml  # pip install pyyaml


def posix(p):
    """Return forward-slash path."""
    return str(Path(p).as_posix())


def load_yaml(path):
    """Load YAML."""
    with open(posix(path), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_user_settings(path):
    """Return (symbol, timeframe) from BB_USER_SETTINGS.yaml."""
    data = load_yaml(path)
    return str(data["SYSTEM_SYMBOL"]), str(data["SYSTEM_TIMEFRAME"])


def pluck(container, key):
    """One-level descent supporting dict or list-of-dicts."""
    if isinstance(container, dict) and key in container:
        return container[key]
    if isinstance(container, list):
        for item in container:
            if isinstance(item, dict) and key in item:
                return item[key]
    raise KeyError(key)


def traverse(root, keys):
    """Walk through nested structure using keys with list/dict tolerance."""
    node = root
    for k in keys:
        node = pluck(node, k)
    return node


def select_candle(candles, candle_index):
    """Select record by CANDLE==index; fallback to positional index."""
    flat = []
    if isinstance(candles, dict):
        flat = [candles]
    elif isinstance(candles, list):
        for it in candles:
            if isinstance(it, dict):
                flat.append(it)
            elif isinstance(it, list):
                for sub in it:
                    if isinstance(sub, dict):
                        flat.append(sub)
    else:
        raise TypeError("Unexpected candles structure")

    for rec in flat:
        if rec.get("CANDLE") == candle_index:
            return rec
    if 0 <= candle_index < len(flat):
        return flat[candle_index]
    raise IndexError("candle not found")


def read_value_as_str(path, symbol, timeframe, candle_index, value_key):
    """Read value as string following required nesting."""
    data = load_yaml(path)
    candles = traverse(data, ["BINANCE_FUTURES", symbol, timeframe])
    rec = select_candle(candles, candle_index)
    return str(rec[value_key])


def parse_float_maybe(s):
    """Try parsing float; return (value, ok)."""
    try:
        return float(str(s).strip()), True
    except Exception:
        return 0.0, False


def tri_compare(a_str, b_str, op):
    """
    Return decision: True/False/None
    - For '>' or '<' if values are equal (numeric if both parseable else string), return None (NO_ACTION).
    """
    if op in (">", "<", ">=", "<="):
        af, ok_a = parse_float_maybe(a_str)
        bf, ok_b = parse_float_maybe(b_str)
        if ok_a and ok_b:
            if op in (">", "<") and af == bf:
                return None
            if op == ">":
                return af > bf
            if op == "<":
                return af < bf
            if op == ">=":
                return af >= bf
            if op == "<=":
                return af <= bf
        else:
            if op in (">", "<") and a_str == b_str:
                return None
            if op == ">":
                return a_str > b_str
            if op == "<":
                return a_str < b_str
            if op == ">=":
                return a_str >= b_str
            if op == "<=":
                return a_str <= b_str
    if op == "==":
        return a_str == b_str
    if op == "!=":
        return a_str != b_str
    raise ValueError("Unsupported operator")


def run_scripts(scripts):
    """Run scripts sequentially with current Python interpreter. No printing here."""
    for script in scripts:
        cmd = [sys.executable, posix(script)]
        rc = subprocess.run(cmd, check=False).returncode
        if rc != 0:
            sys.exit(rc)


def main():
    symbol, timeframe = read_user_settings(USER_SETTINGS_PATH)

    a_val = read_value_as_str(A_PATH, symbol, timeframe, A_CANDLE, A_VALUE_KEY)
    z_val = read_value_as_str(Z_PATH, symbol, timeframe, Z_CANDLE, Z_VALUE_KEY)

    decision = tri_compare(a_val, z_val, COMPARISON_OPERATOR)

    # Execute scripts based on decision
    if decision is True:
        run_scripts(SCRIPTS_TRUE)
    elif decision is False:
        run_scripts(SCRIPTS_FALSE)
    else:
        # None -> NO_ACTION for '>' or '<' when equal
        pass


if __name__ == "__main__":
    main()
