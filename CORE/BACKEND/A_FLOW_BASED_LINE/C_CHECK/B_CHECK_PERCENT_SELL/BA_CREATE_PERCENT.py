# -*- coding: utf-8 -*-
"""
Compute percent change between CLOSE_PRICE and OPEN_PRICE from AA_CANDLE.yaml
and write the result into CC_TRIGGERS_CONFIG.yaml under PERCENT_STATUS only.

Notes:
- Preserves original formatting/comments via ruamel.yaml round-trip.
- Robustly navigates either list-of-singleton-maps or plain mappings for symbol/timeframe.
- Recursively finds and updates the first occurrence of PERCENT_STATUS; does not restructure other keys.
- Comments are in English as requested.
"""

# =========================
# Settings (top of script)
# =========================
BB_USER_SETTINGS_PATH = "CORE/DATA/BB_USER_SETTINGS.yaml"    # read SYSTEM_SYMBOL & SYSTEM_TIMEFRAME
AA_CANDLE_PATH        = "CORE/DATA/AA_CANDLE.yaml"           # read BINANCE_FUTURES -> {symbol} -> {timeframe}
CC_TRIGGERS_PATH      = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"  # update PERCENT_STATUS only

TARGET_KEY            = "PERCENT_STATUS"                     # key to update in CC_TRIGGERS_CONFIG.yaml
MAX_DECIMALS          = 3                                    # round to at most this many decimals

# Keys for price fields
KEY_OPEN_PRICE        = "OPEN_PRICE"
KEY_CLOSE_PRICE       = "CLOSE_PRICE"

# Candle selection
CANDLE_INDEX_KEY      = "CANDLE"                             # field name that holds the candle index
CANDLE_INDEX_VALUE    = 0                                    # choose the candle with this index

# =========================
# Logic (generic names)
# =========================
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from typing import Any, Tuple, Optional, Union

YamlMap = Union[dict, CommentedMap]
YamlSeq = Union[list, CommentedSeq]

def _yaml_rt() -> YAML:
    """Create a configured round-trip YAML instance."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=2)
    return yaml

def _load_yaml(path: str) -> Any:
    """Load YAML with round-trip support to preserve formatting and comments."""
    yaml = _yaml_rt()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    return data

def _dump_yaml(path: str, data: Any) -> None:
    """Dump YAML preserving original style."""
    yaml = _yaml_rt()
    with open(path, "w", encoding="utf-8", newline="") as f:
        yaml.dump(data, f)

def _get_from_map_or_seq(root: Union[YamlMap, YamlSeq], key: str) -> Any:
    """
    Return value by key from either:
      - mapping: root[key]
      - list of singleton maps: first item where key in item, return item[key]
    """
    if isinstance(root, (dict, CommentedMap)):
        if key in root:
            return root[key]
        raise KeyError(f"Key '{key}' not found in mapping")
    if isinstance(root, (list, CommentedSeq)):
        for item in root:
            if isinstance(item, (dict, CommentedMap)) and key in item:
                return item[key]
        raise KeyError(f"Key '{key}' not found in sequence of maps")
    raise TypeError(f"Unsupported YAML node type: {type(root).__name__}")

def _find_candle(seq: YamlSeq, idx_key: str, idx_value: Any) -> YamlMap:
    """Find candle mapping in a sequence where item[idx_key] == idx_value."""
    if not isinstance(seq, (list, CommentedSeq)):
        raise TypeError("Expected a sequence (list) of candles")
    for item in seq:
        if isinstance(item, (dict, CommentedMap)) and idx_key in item and item[idx_key] == idx_value:
            return item
    raise KeyError(f"No candle entry found with {idx_key} == {idx_value}")

def _to_float(value: Any, name: str) -> float:
    """Convert YAML scalar to float safely."""
    try:
        return float(value)
    except Exception as e:
        raise ValueError(f"Cannot parse {name}='{value}' as float") from e

def _round_max_decimals(value: float, max_decimals: int) -> float:
    """Round a float to at most 'max_decimals' digits after decimal point."""
    return round(value, max_decimals)

def _update_first_key_recursive(node: Any, target_key: str, new_value: Any) -> bool:
    """
    Recursively locate the first occurrence of 'target_key' within a YAML structure
    and update it to 'new_value'. Returns True if updated, False otherwise.
    """
    if isinstance(node, (dict, CommentedMap)):
        if target_key in node:
            node[target_key] = new_value  # preserve scalar style by assigning directly
            return True
        for v in node.values():
            if _update_first_key_recursive(v, target_key, new_value):
                return True
    elif isinstance(node, (list, CommentedSeq)):
        for item in node:
            if _update_first_key_recursive(item, target_key, new_value):
                return True
    return False

def _extract_prices(candles_root: Any, system_symbol: str, system_timeframe: str) -> Tuple[float, float]:
    """Navigate AA_CANDLE.yaml and return (open_price, close_price) for the requested symbol/timeframe/candle index."""
    if not isinstance(candles_root, (dict, CommentedMap)) or "BINANCE_FUTURES" not in candles_root:
        raise KeyError("BINANCE_FUTURES section not found in AA_CANDLE.yaml")

    bf_section = candles_root["BINANCE_FUTURES"]  # may be a list (seq) of singleton maps
    symbol_block = _get_from_map_or_seq(bf_section, system_symbol)
    timeframe_block = _get_from_map_or_seq(symbol_block, system_timeframe)

    # timeframe_block must be a sequence of candle maps
    candle = _find_candle(timeframe_block, CANDLE_INDEX_KEY, CANDLE_INDEX_VALUE)

    if KEY_OPEN_PRICE not in candle or KEY_CLOSE_PRICE not in candle:
        missing = [k for k in (KEY_OPEN_PRICE, KEY_CLOSE_PRICE) if k not in candle]
        raise KeyError(f"Missing required price keys in candle: {missing}")

    open_price = _to_float(candle[KEY_OPEN_PRICE], KEY_OPEN_PRICE)
    close_price = _to_float(candle[KEY_CLOSE_PRICE], KEY_CLOSE_PRICE)
    return open_price, close_price

def main():
    # Read system symbol and timeframe
    settings = _load_yaml(BB_USER_SETTINGS_PATH)
    if not isinstance(settings, (dict, CommentedMap)):
        raise ValueError("BB_USER_SETTINGS.yaml must be a mapping with SYSTEM_SYMBOL and SYSTEM_TIMEFRAME")

    if "SYSTEM_SYMBOL" not in settings or "SYSTEM_TIMEFRAME" not in settings:
        raise KeyError("SYSTEM_SYMBOL and/or SYSTEM_TIMEFRAME not found in BB_USER_SETTINGS.yaml")

    system_symbol = str(settings["SYSTEM_SYMBOL"])
    system_timeframe = str(settings["SYSTEM_TIMEFRAME"])

    # Read candle structure and extract prices
    candles_root = _load_yaml(AA_CANDLE_PATH)
    open_price, close_price = _extract_prices(candles_root, system_symbol, system_timeframe)

    if open_price == 0:
        raise ZeroDivisionError("OPEN_PRICE is zero; cannot compute percent change")

    # Compute signed percent change: ((close - open) / open) * 100
    percent_value = ((close_price - open_price) / open_price) * 100.0
    percent_value = _round_max_decimals(percent_value, MAX_DECIMALS)

    # Load triggers config and update only the first occurrence of TARGET_KEY
    triggers = _load_yaml(CC_TRIGGERS_PATH)
    if not _update_first_key_recursive(triggers, TARGET_KEY, percent_value):
        # If not found anywhere, leave file unchanged and fail loudly (to avoid unintended structure changes)
        raise KeyError(f"Key '{TARGET_KEY}' not found anywhere in CC_TRIGGERS_CONFIG.yaml")

    # Write back preserving original formatting and comments
    _dump_yaml(CC_TRIGGERS_PATH, triggers)

if __name__ == "__main__":
    main()
