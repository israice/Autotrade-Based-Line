import yaml
import requests
import datetime
import time
import os
import socket  # Added for error checking

# =========================
# Settings (top of script)
# =========================
settings_path = 'settings.yaml'
output_path = 'CORE/DATA/AA_CANDLE.yaml'
api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'
symbol_key = 'SYSTEM_SYMBOL'
interval_key = 'SYSTEM_TIMEFRAME'
limit = 1
max_retries = 3  # Configurable retry count

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

# =========================
# Load settings
# =========================
with open(settings_path, 'r') as f:
    settings = yaml.safe_load(f)

SYSTEM_SYMBOL = settings[symbol_key]
interval = settings[interval_key]

# =========================
# Logic (bottom of script)
# =========================
# Start timer
start_time = time.time()

# Prepare API params
params = {
    'symbol': SYSTEM_SYMBOL,
    'interval': interval,
    'limit': limit
}

# Fetch data with retries
candles = None
for attempt in range(max_retries):
    try:
        response = requests.get(f"{api_base_url}{api_endpoint}", params=params, timeout=10)
        response.raise_for_status()
        candles = response.json()
        break  # Success, exit the loop
    except requests.exceptions.RequestException as e:
        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {2 ** attempt} seconds...")
        time.sleep(2 ** attempt)  # Exponential backoff: 1, 2, 4 seconds
else:
    # All retries failed
    final_error = e  # Capture the last error
    if isinstance(final_error.__cause__, socket.gaierror):
        print(f"DNS resolution failed for '{api_base_url}': {final_error}. Recommendations: Check internet/DNS (try Google's 8.8.8.8), use VPN, or verify if domain is blocked in your region.")
    else:
        print(f"Request failed after {max_retries} retries: {final_error}")
    print("Alternative: Use WebSocket stream 'wss://fstream.binance.com/ws/<symbol>@kline_<interval>' for real-time data, or download historical klines from https://data.binance.vision/.")
    raise  # Re-raise to stop execution or handle further

# Proceed if successful
fetch_timestamp_ms = fmt_ms_now_utc()

candle_entries = []

# Reverse to have latest first (CANDLE: 0 == latest)
for idx in range(len(candles) - 1, -1, -1):
    c = candles[idx]
    candle_idx = len(candles) - 1 - idx  # 0 for latest

    entry = {
        'CANDLE': candle_idx,
        'CLOSE_TIME': fmt_ms_from_epoch(int(c[6])),  # kline close time (ms)
        'TIMESTAMP': fetch_timestamp_ms,             # fetch time (ms precision)
        'OPEN_TIME': fmt_ms_from_epoch(int(c[0])),   # kline open time (ms)
        'HIGH_PRICE': float(c[2]),
        'CLOSE_PRICE': float(c[4]),
        'OPEN_PRICE': float(c[1]),
        'LOW_PRICE': float(c[3]),
    }
    candle_entries.append(entry)

output_data = {
    'BINANCE_FUTURES': [
        {
            SYSTEM_SYMBOL: [
                {
                    interval: candle_entries
                }
            ]
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
# print(f"- - - - << {limit} >> candles << {interval} >> timeframe for << {SYSTEM_SYMBOL} >> at {current_time} (took {exec_time:.3f}s)")
