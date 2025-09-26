# -*- coding: utf-8 -*-
"""
Minimal round-trip updater:
- Read OPEN_PRICE and CLOSE_PRICE for chosen symbol/timeframe/candle from AA_CANDLE.yaml
- Compute percent change
- Replace only the value of PERCENT_STATUS in CC_TRIGGERS_CONFIG.yaml
- Preserve ordering, comments, and (when applicable) quoting style of PERCENT_STATUS

Comments are in English as requested.
"""

# =========================
# Settings (top of script)
# =========================
BB_USER_SETTINGS_PATH = "settings.yaml"     # provides SYSTEM_SYMBOL and SYSTEM_TIMEFRAME
AA_CANDLE_PATH        = "CORE/DATA/AA_CANDLE.yaml"            # source of candle data
CC_TRIGGERS_PATH      = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"   # destination to update

TARGET_KEY            = "PERCENT_STATUS"                      # key to replace (must exist)
MAX_DECIMALS          = 3                                     # round percent to at most N decimals

# Candle selection
CANDLE_INDEX_KEY      = "CANDLE"
CANDLE_INDEX_VALUE    = 0

# =========================
# Logic (generic names)
# =========================
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, SingleQuotedScalarString

def _yaml_rt() -> YAML:
    """Configure ruamel.yaml in round-trip mode to preserve formatting."""
    y = YAML(typ="rt")
    y.preserve_quotes = True
    y.indent(mapping=2, sequence=2, offset=2)
    return y

def _load_rt(path):
    """Load YAML preserving style."""
    y = _yaml_rt()
    with open(path, "r", encoding="utf-8") as f:
        data = y.load(f)
    return data

def _dump_rt(path, data):
    """Dump YAML preserving style."""
    y = _yaml_rt()
    with open(path, "w", encoding="utf-8", newline="") as f:
        y.dump(data, f)

def _find_in_seq_by_key(seq: CommentedSeq, key: str):
    """Find value under the first mapping in sequence that contains 'key'."""
    for item in seq:
        if isinstance(item, (dict, CommentedMap)) and key in item:
            return item[key]
    raise KeyError(f"Key '{key}' not found in sequence")

def _find_candle(seq: CommentedSeq, idx_key: str, idx_value):
    """Locate candle dict where seq[i][idx_key] == idx_value."""
    for item in seq:
        if isinstance(item, (dict, CommentedMap)) and item.get(idx_key) == idx_value:
            return item
    raise KeyError(f"No candle entry with {idx_key} == {idx_value}")

def _round_at_most(x: float, max_decimals: int) -> float:
    """Round to at most N decimals (no forced trailing zeros)."""
    return round(x, max_decimals)

def _as_like_existing(new_number: float, existing_scalar):
    """
    Return 'new_number' formatted to match existing scalar style:
    - If existing was quoted string, keep the same quote type.
    - Otherwise, return as float scalar.
    """
    # Build string with trimmed trailing zeros if we choose to keep it as string
    s = f"{new_number:.{MAX_DECIMALS}f}".rstrip("0").rstrip(".")
    if isinstance(existing_scalar, DoubleQuotedScalarString):
        return DoubleQuotedScalarString(s)
    if isinstance(existing_scalar, SingleQuotedScalarString):
        return SingleQuotedScalarString(s)
    if isinstance(existing_scalar, str):
        # Plain (unquoted) string originally -> keep plain string
        return s
    # Default: return as float to keep numeric scalar
    return new_number

def main():
    # --- Read settings ---
    settings = _load_rt(BB_USER_SETTINGS_PATH)
    symbol = str(settings["SYSTEM_SYMBOL"])
    timeframe = str(settings["SYSTEM_TIMEFRAME"])

    # --- Read candle source (only read; we do not write this file) ---
    candles_root = _load_rt(AA_CANDLE_PATH)
    bf = candles_root["BINANCE_FUTURES"]                     # sequence: - {symbol: ...}
    sym_block = _find_in_seq_by_key(bf, symbol)              # sequence: - {timeframe: ...}
    tf_block = _find_in_seq_by_key(sym_block, timeframe)     # sequence: - {CANDLE: 0, ...}

    candle = _find_candle(tf_block, CANDLE_INDEX_KEY, CANDLE_INDEX_VALUE)
    open_price = float(candle["OPEN_PRICE"])
    close_price = float(candle["CLOSE_PRICE"])

    # --- Compute percent change ---
    percent = 0.0 if open_price == 0.0 else ((close_price - open_price) / open_price) * 100.0
    percent = _round_at_most(percent, MAX_DECIMALS)

    # --- Open triggers, replace only the scalar value for TARGET_KEY ---
    triggers = _load_rt(CC_TRIGGERS_PATH)
    if TARGET_KEY not in triggers:
        raise KeyError(f"'{TARGET_KEY}' not found in {CC_TRIGGERS_PATH}; replacement only is required.")

    # Preserve quoting style of existing scalar if any
    existing = triggers[TARGET_KEY]
    triggers[TARGET_KEY] = _as_like_existing(percent, existing)

    # --- Write back preserving layout; only that value is changed ---
    _dump_rt(CC_TRIGGERS_PATH, triggers)

if __name__ == "__main__":
    main()
