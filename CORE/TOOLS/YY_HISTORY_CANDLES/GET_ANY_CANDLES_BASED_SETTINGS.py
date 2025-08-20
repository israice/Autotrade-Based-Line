import yaml
import requests
import datetime
import time
import os
import socket  # Used for network/DNS error hints
from copy import deepcopy

# =========================
# Settings (top of script)
# =========================
# User/settings files
user_settings_path = 'CORE/DATA/BB_USER_SETTINGS.yaml'       # provides SYSTEM_SYMBOL
triggers_config_path = 'CORE/DATA/CC_TRIGGERS_CONFIG.yaml'    # provides GET_CANDLE_NUMBER, GET_ALL_INTERVALS
output_path = 'CORE/DATA/YY_HISTORY_CANDLES.yaml'

# API settings
api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'

# Keys inside user settings
symbol_key = 'SYSTEM_SYMBOL'
interval_key = 'SYSTEM_TIMEFRAME'  # Kept for compatibility; not used in logic

# Networking/retries
max_retries = 3           # Retry count per HTTP request
http_timeout_sec = 10

# Safety caps for REST fetch size
MIN_EXTRA_FOR_SAFETY = 5  # ask a few extra to handle an in-progress bar at the end
MAX_HTTP_LIMIT = 1500     # Binance hard cap

# =========================
# Helpers (format/time/etc.)
# =========================
def fmt_ms_from_epoch(ms: int) -> str:
    """Format epoch milliseconds to 'YYYY-MM-DD HH:MM:SS:mmm' in UTC."""
    dt = datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC)
    return dt.strftime('%Y-%m-%d %H:%M:%S') + f':{int(ms % 1000):03d}'

def fmt_ms_now_utc() -> str:
    """Current UTC time formatted as 'YYYY-MM-DD HH:MM:SS:mmm'."""
    dt = datetime.datetime.now(datetime.UTC)
    return dt.strftime('%Y-%m-%d %H:%M:%S') + f':{dt.microsecond // 1000:03d}'

def fetch_klines_with_retries(params: dict, retries: int) -> list:
    """Fetch klines with retry logic; raise last exception if all retries fail."""
    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.get(f"{api_base_url}{api_endpoint}", params=params, timeout=http_timeout_sec)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            last_exc = e
            backoff = 2 ** attempt
            print(f"Attempt {attempt + 1} failed for {params.get('interval')} - {e}. Retrying in {backoff} seconds...")
            time.sleep(backoff)
    # All retries failed
    if isinstance(getattr(last_exc, '__cause__', None), socket.gaierror):
        print(f"DNS resolution failed for '{api_base_url}': {last_exc}. "
              f"Recommendations: Check internet/DNS (e.g., 8.8.8.8), use VPN, or verify regional access.")
    else:
        print(f"Request for interval {params.get('interval')} failed after {retries} retries: {last_exc}")
    print("Alternative: Use WebSocket stream 'wss://fstream.binance.com/ws/<symbol>@kline_<interval>' "
          "for real-time data, or download historical klines from https://data.binance.vision/.")
    raise last_exc

def closed_candles_only(raw_klines: list) -> list:
    """Return only CLOSED klines based on close_time <= now."""
    now_ms = int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
    return [c for c in raw_klines if int(c[6]) <= now_ms]

def select_closed_by_index(raw_klines: list, idx_from_latest: int) -> list | None:
    """
    From raw klines (oldest->newest), pick CLOSED candle by index from latest closed.
    idx_from_latest: 0 -> latest closed, 1 -> previous closed, etc.
    Returns kline array or None if not enough data.
    """
    closed = closed_candles_only(raw_klines)
    if len(closed) <= idx_from_latest:
        return None
    return closed[-(idx_from_latest + 1)]

def load_existing_map(path: str, symbol: str) -> dict:
    """Load existing YAML and return {interval: [entries]} for the given symbol."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    mapping = {}
    try:
        bf_list = data.get('BINANCE_FUTURES', [])
        for obj in bf_list:
            if symbol in obj:
                items = obj[symbol] or []
                for item in items:
                    # item is like { "1m": [ ... ] }
                    for k, v in item.items():
                        mapping[k] = v or []
                break
    except Exception:
        pass
    return mapping

def build_output_data(symbol: str, mapping: dict, order: list[str]) -> dict:
    """Build YAML structure from {interval: [entries]} preserving 'order' first."""
    blocks = []
    seen = set()
    for itv in order:
        if itv in mapping:
            blocks.append({itv: mapping[itv]})
            seen.add(itv)
    # Append remaining intervals not in 'order' (kept as-is)
    for itv, entries in mapping.items():
        if itv not in seen:
            blocks.append({itv: entries})
    return {
        'BINANCE_FUTURES': [
            {
                symbol: blocks
            }
        ]
    }

def normalize_intervals(obj) -> list[str]:
    """Ensure intervals is a list[str] with non-empty values."""
    if isinstance(obj, list):
        return [str(x).strip() for x in obj if str(x).strip()]
    return []

# =========================
# Load settings
# =========================
# Load symbol
with open(user_settings_path, 'r') as f:
    user_settings = yaml.safe_load(f) or {}
SYSTEM_SYMBOL = user_settings.get(symbol_key)
_ = user_settings.get(interval_key, None)  # compatibility; not used

if not SYSTEM_SYMBOL:
    raise ValueError(f"Missing '{symbol_key}' in {user_settings_path}")

# Load triggers config (candle index and intervals)
with open(triggers_config_path, 'r') as f:
    trig = yaml.safe_load(f) or {}

TARGET_INSERT_INDEX = int(trig.get('GET_CANDLE_NUMBER', 1))
if TARGET_INSERT_INDEX < 0:
    raise ValueError("GET_CANDLE_NUMBER must be >= 0")

ALL_INTERVALS = normalize_intervals(trig.get('GET_ALL_INTERVALS'))
if not ALL_INTERVALS:
    raise ValueError(f"GET_ALL_INTERVALS is empty or missing in {triggers_config_path}")

# =========================
# Logic (bottom of script)
# =========================
start_time = time.time()
fetch_timestamp_str = fmt_ms_now_utc()  # One fetch timestamp for all intervals

# Compute REST 'limit' dynamically to cover requested index and a safety margin
need_closed = TARGET_INSERT_INDEX + 1              # how many CLOSED candles we must be able to see
hist_fetch_limit = min(max(need_closed + MIN_EXTRA_FOR_SAFETY, 2), MAX_HTTP_LIMIT)

# Load existing per-interval entries for this symbol
existing_map = load_existing_map(output_path, SYSTEM_SYMBOL)
new_map = deepcopy(existing_map)

for interval in ALL_INTERVALS:
    # Prepare API params to get enough klines to resolve the requested index
    params = {
        'symbol': SYSTEM_SYMBOL,
        'interval': interval,
        'limit': hist_fetch_limit
    }

    raw_klines = fetch_klines_with_retries(params, max_retries)
    chosen = select_closed_by_index(raw_klines, TARGET_INSERT_INDEX)
    if chosen is None:
        # Not enough closed data for this interval; skip safely
        # print(f"Skip {interval}: not enough closed klines for index {TARGET_INSERT_INDEX}")
        continue

    insert_entry = {
        'CANDLE': int(TARGET_INSERT_INDEX),              # insert at requested index
        'CLOSE_TIME': fmt_ms_from_epoch(int(chosen[6])),
        'TIMESTAMP': fetch_timestamp_str,                # insertion/fetch timestamp
        'OPEN_TIME': fmt_ms_from_epoch(int(chosen[0])),
        'HIGH_PRICE': float(chosen[2]),
        'CLOSE_PRICE': float(chosen[4]),
        'OPEN_PRICE': float(chosen[1]),
        'LOW_PRICE': float(chosen[3]),
    }

    # Get existing entries for this interval (if any)
    entries = deepcopy(existing_map.get(interval, []))

    # Keep entries with CANDLE < TARGET_INSERT_INDEX as-is; shift CANDLE >= TARGET_INSERT_INDEX by +1
    lower = []
    shifted = []
    for e in entries:
        if isinstance(e, dict) and isinstance(e.get('CANDLE'), int):
            if e['CANDLE'] < TARGET_INSERT_INDEX:
                lower.append(e)
            else:
                e2 = deepcopy(e)
                e2['CANDLE'] = e['CANDLE'] + 1
                shifted.append(e2)
        else:
            # If entry doesn't follow schema, keep it at the end untouched
            shifted.append(e)

    # Sort both parts to maintain ascending CANDLE order
    lower_sorted = sorted(lower, key=lambda x: x.get('CANDLE', -1))
    shifted_sorted = sorted(
        shifted,
        key=lambda x: (x.get('CANDLE') if isinstance(x, dict) and isinstance(x.get('CANDLE'), int) else 10**9)
    )

    # Build the updated list: [lower (<TARGET)], new insert at TARGET, then shifted (>=TARGET+1)
    updated_entries = lower_sorted + [insert_entry] + shifted_sorted

    new_map[interval] = updated_entries

# Compose and save YAML
output_data = build_output_data(SYSTEM_SYMBOL, new_map, ALL_INTERVALS)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w') as f:
    yaml.safe_dump(output_data, f, default_flow_style=False, sort_keys=False)

# Execution time logging (silent by default)
exec_time = time.time() - start_time
current_time = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
# print(f"- - - - Inserted historical candle at index {TARGET_INSERT_INDEX} for << {SYSTEM_SYMBOL} >> at {current_time} (took {exec_time:.3f}s)")
