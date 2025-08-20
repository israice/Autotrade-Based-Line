import yaml
import requests
import datetime
import time
import os
import socket

# =========================
# Settings (top of script)
# =========================
settings_path      = 'CORE/DATA/BB_USER_SETTINGS.yaml'
output_path        = 'CORE/DATA/YY_HISTORY_CANDLES.yaml'

api_base_url       = 'https://fapi.binance.com'
api_klines_ep      = '/fapi/v1/klines'
api_time_ep        = '/fapi/v1/time'

symbol_key         = 'SYSTEM_SYMBOL'
interval_key       = 'SYSTEM_TIMEFRAME'

TARGET_CANDLE_NUM  = 2   # candle_N to fetch & insert (1 = last closed, 2 = previous, 3 = previous-2, ...)
REQUEST_LIMIT      = 1   # fetch exactly one kline
MAX_RETRIES        = 3
HTTP_TIMEOUT       = 10

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

def get_server_time_ms() -> int:
    """Return Binance server time in ms (avoid local clock drift)."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(f"{api_base_url}{api_time_ep}", timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            return int(r.json()['serverTime'])
        except requests.exceptions.RequestException as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch server time: {last_err}")

def interval_ms(iv: str) -> int | None:
    """Fixed-size interval to ms; returns None for '1M' (handled separately)."""
    m = {
        '1m': 60_000, '3m': 180_000, '5m': 300_000, '15m': 900_000, '30m': 1_800_000,
        '1h': 3_600_000, '2h': 7_200_000, '4h': 14_400_000, '6h': 21_600_000,
        '8h': 28_800_000, '12h': 43_200_000,
        '1d': 86_400_000, '3d': 259_200_000,
        '1w': 604_800_000,
        # '1M' is variable length
    }
    return m.get(iv)

def floor_fixed_interval(ts_ms: int, iv_ms: int) -> int:
    """Floor epoch ms to start of fixed-size interval (UTC)."""
    return (ts_ms // iv_ms) * iv_ms

def month_open_ms(ts_ms: int) -> int:
    """Get month-open (UTC) for timestamp in ms."""
    dt = datetime.datetime.fromtimestamp(ts_ms / 1000, datetime.UTC)
    dt0 = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(dt0.timestamp() * 1000)

def add_months_from_open(month_open_ms_val: int, delta_months: int) -> int:
    """Shift month-open ms by delta months."""
    dt = datetime.datetime.fromtimestamp(month_open_ms_val / 1000, datetime.UTC)
    y, m = dt.year, dt.month
    idx = y * 12 + (m - 1) + delta_months
    y2, m2 = divmod(idx, 12)
    m2 += 1
    dt2 = datetime.datetime(y2, m2, 1, 0, 0, 0, 0, tzinfo=datetime.UTC)
    return int(dt2.timestamp() * 1000)

def ensure_structure(root: dict, symbol: str, tf: str) -> list:
    """
    Ensure structure:
    BINANCE_FUTURES -> [ { SYMBOL: [ { timeframe: [entries] } ] } ]
    Return the list that holds candle entries for (symbol, timeframe).
    """
    if 'BINANCE_FUTURES' not in root or not isinstance(root['BINANCE_FUTURES'], list):
        root['BINANCE_FUTURES'] = []

    sym_obj = None
    for item in root['BINANCE_FUTURES']:
        if isinstance(item, dict) and symbol in item:
            sym_obj = item
            break
    if sym_obj is None:
        sym_obj = {symbol: []}
        root['BINANCE_FUTURES'].append(sym_obj)

    lst = sym_obj[symbol]
    if not isinstance(lst, list):
        lst = []
        sym_obj[symbol] = lst

    tf_obj = None
    for item in lst:
        if isinstance(item, dict) and tf in item:
            tf_obj = item
            break
    if tf_obj is None:
        tf_obj = {tf: []}
        lst.append(tf_obj)

    entries = tf_obj[tf]
    if not isinstance(entries, list):
        entries = []
        tf_obj[tf] = entries

    return entries

def reindex_from_one(entries: list) -> None:
    """Set CANDLE starting from 1 at the top (newest at index 0)."""
    for i, e in enumerate(entries):
        e['CANDLE'] = i + 1  # keep key order; assumes 'CANDLE' already present

def enforce_field_order_inplace(entries: list) -> None:
    """
    Ensure key order in each entry:
    CANDLE, CLOSE_TIME, TIMESTAMP, OPEN_TIME, HIGH_PRICE, CLOSE_PRICE, OPEN_PRICE, LOW_PRICE, then any extras.
    """
    desired = ['CANDLE','CLOSE_TIME','TIMESTAMP','OPEN_TIME','HIGH_PRICE','CLOSE_PRICE','OPEN_PRICE','LOW_PRICE']
    for i, e in enumerate(entries):
        new_e = {}
        for k in desired:
            if k in e:
                new_e[k] = e[k]
        # append any extra keys, preserving their original order
        for k in e:
            if k not in new_e:
                new_e[k] = e[k]
        entries[i] = new_e  # replace in-place at list index

# =========================
# Load settings
# =========================
with open(settings_path, 'r') as f:
    settings = yaml.safe_load(f)

SYSTEM_SYMBOL = settings[symbol_key]
TIMEFRAME     = settings[interval_key]
IV_MS         = interval_ms(TIMEFRAME)  # None if '1M'

# =========================
# Logic (bottom of script)
# =========================
# Load existing YAML
if os.path.exists(output_path):
    with open(output_path, 'r') as f:
        try:
            output_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            output_data = {}
else:
    output_data = {}

entries = ensure_structure(output_data, SYSTEM_SYMBOL, TIMEFRAME)

# Keep newest at top: sort by CANDLE ascending (1,2,3,...) and enforce order
entries.sort(key=lambda e: e.get('CANDLE', 1))
enforce_field_order_inplace(entries)  # normalize before reindex

# Compute open time of candle_1 (last closed) using server time
server_now = get_server_time_ms()
if TIMEFRAME == '1M':
    ref_open_ms = add_months_from_open(month_open_ms(server_now), -1)
else:
    if IV_MS is None:
        raise ValueError("Interval mapping error.")
    ref_open_ms = floor_fixed_interval(server_now, IV_MS) - IV_MS

# Compute desired candle_N boundaries:
# N = TARGET_CANDLE_NUM; candle_1 = last closed; candle_2 = previous; etc.
N = int(TARGET_CANDLE_NUM)
if N < 1:
    raise ValueError("TARGET_CANDLE_NUM must be >= 1 (no candle_0).")

if TIMEFRAME == '1M':
    desired_open_ms = add_months_from_open(ref_open_ms, -(N - 1))
    next_open_ms    = add_months_from_open(desired_open_ms, 1)
else:
    desired_open_ms = ref_open_ms - (N - 1) * IV_MS
    next_open_ms    = desired_open_ms + IV_MS

start_ms = desired_open_ms
end_ms   = next_open_ms - 1  # inclusive top bound to stay inside the candle window

# Fetch exactly one closed historical candle in the strict window
params = {
    'symbol': SYSTEM_SYMBOL,
    'interval': TIMEFRAME,
    'limit': REQUEST_LIMIT,
    'startTime': start_ms,
    'endTime': end_ms
}

last_err = None
for attempt in range(MAX_RETRIES):
    try:
        r = requests.get(f"{api_base_url}{api_klines_ep}", params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        klines = r.json()
        break
    except requests.exceptions.RequestException as e:
        last_err = e
        time.sleep(2 ** attempt)
else:
    raise RuntimeError(f"Failed to fetch klines: {last_err}")

if not isinstance(klines, list) or len(klines) < 1:
    raise RuntimeError("Requested historical kline not returned by Binance within the specified window.")

k = klines[0]  # exactly one expected
fetch_ts = fmt_ms_now_utc()

# Build new entry with CANDLE key first to preserve order
new_entry = {
    'CANDLE': N,  # placeholder; will be reindexed below but stays first in order
    'CLOSE_TIME': fmt_ms_from_epoch(int(k[6])),
    'TIMESTAMP':  fetch_ts,
    'OPEN_TIME':  fmt_ms_from_epoch(int(k[0])),
    'HIGH_PRICE': float(k[2]),
    'CLOSE_PRICE': float(k[4]),
    'OPEN_PRICE': float(k[1]),
    'LOW_PRICE':  float(k[3]),
}

# Insert at position (N-1), pushing older ones down
insert_pos = max(0, N - 1)
if insert_pos > len(entries):
    insert_pos = len(entries)  # append if list shorter
entries.insert(insert_pos, new_entry)

# Reindex so that top is candle_1, then candle_2, etc. (CANDLE already first)
reindex_from_one(entries)

# Enforce field order again after reindex (for all entries)
enforce_field_order_inplace(entries)

# Persist YAML with insertion order preserved
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w') as f:
    yaml.safe_dump(output_data, f, default_flow_style=False, sort_keys=False)
