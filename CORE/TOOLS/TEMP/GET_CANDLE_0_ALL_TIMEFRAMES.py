import yaml
import requests
import datetime
import time
import os
import socket  # Used for network/DNS error hints

# =========================
# Settings (top of script)
# =========================
settings_path = 'settings.yaml'
output_path = 'CORE/DATA/YY_HISTORY_CANDLES.yaml'

api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'

symbol_key = 'SYSTEM_SYMBOL'
interval_key = 'SYSTEM_TIMEFRAME'  # Kept for compatibility; not used when fetching ALL intervals
limit = 1
max_retries = 3  # Retry count per request

# Binance Futures supported intervals to fetch (one candle from each)
ALL_INTERVALS = [
    '1m', '3m', '5m', '15m', '30m',
    '1h', '2h', '4h', '6h', '8h', '12h',
    '1d', '3d', '1w', '1M'
]

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
            response = requests.get(f"{api_base_url}{api_endpoint}", params=params, timeout=10)
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

# =========================
# Load settings
# =========================
with open(settings_path, 'r') as f:
    settings = yaml.safe_load(f)

SYSTEM_SYMBOL = settings[symbol_key]
# Keeping this read for compatibility/info, but we fetch ALL intervals below
_ = settings.get(interval_key, None)

# =========================
# Logic (bottom of script)
# =========================
start_time = time.time()
fetch_timestamp_str = fmt_ms_now_utc()  # Single fetch timestamp for all intervals

symbol_intervals_block = []  # Will hold [{interval: [entries]}, ...]

for interval in ALL_INTERVALS:
    # Prepare API params for this interval
    params = {
        'symbol': SYSTEM_SYMBOL,
        'interval': interval,
        'limit': limit
    }

    # Fetch candles for this interval
    candles = fetch_klines_with_retries(params, max_retries)

    # Build entries (latest first; CANDLE: 0 == latest)
    candle_entries = []
    for idx in range(len(candles) - 1, -1, -1):
        c = candles[idx]
        candle_idx = len(candles) - 1 - idx  # 0 for latest
        entry = {
            'CANDLE': candle_idx,
            'CLOSE_TIME': fmt_ms_from_epoch(int(c[6])),  # kline close time (ms)
            'TIMESTAMP': fetch_timestamp_str,            # single fetch time (ms precision)
            'OPEN_TIME': fmt_ms_from_epoch(int(c[0])),   # kline open time (ms)
            'HIGH_PRICE': float(c[2]),
            'CLOSE_PRICE': float(c[4]),
            'OPEN_PRICE': float(c[1]),
            'LOW_PRICE': float(c[3]),
        }
        candle_entries.append(entry)

    # Append this interval block: { "1m": [ {..}, ... ] }
    symbol_intervals_block.append({interval: candle_entries})

# Compose output structure:
# BINANCE_FUTURES -> [{ SYMBOL: [ {interval1: [...]}, {interval2: [...]}, ... ] }]
output_data = {
    'BINANCE_FUTURES': [
        {
            SYSTEM_SYMBOL: symbol_intervals_block
        }
    ]
}

# Save (overwrite) file with the new structure
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w') as f:
    yaml.safe_dump(output_data, f, default_flow_style=False, sort_keys=False)

# Execution time logging
exec_time = time.time() - start_time
current_time = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
# print(f"- - - - Saved << {limit} >> candle per each interval for << {SYSTEM_SYMBOL} >> at {current_time} (took {exec_time:.3f}s)")
