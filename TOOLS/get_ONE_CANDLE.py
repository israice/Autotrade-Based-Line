import yaml
import requests
import datetime
import time
import os
import socket  # Added for error checking

# Settings
settings_path = 'CORE/DATA/user_settings.yaml'
output_path = 'CORE/DATA/A_candle.yaml'
api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'
time_format = '%Y-%m-%d %H:%M:%S'
symbol_key = 'symbol'
interval_key = 'timeframe_interval'
limit = 1
max_retries = 3  # Configurable retry count

# Load settings
with open(settings_path, 'r') as f:
    settings = yaml.safe_load(f)

symbol = settings[symbol_key]
interval = settings[interval_key]

# Start timer
start_time = time.time()

# Prepare API params
params = {
    'symbol': symbol,
    'interval': interval,
    'limit': limit
}

# Fetch data with retries
candles = None
for attempt in range(max_retries):
    try:
        response = requests.get(f"{api_base_url}{api_endpoint}", params=params)
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
fetch_time_str = datetime.datetime.now(datetime.UTC).strftime(time_format)

# Prepare new candle data
new_candles = []
for idx in range(len(candles) - 1, -1, -1):  # Reverse to have latest first
    candle = candles[idx]
    candle_idx = len(candles) - 1 - idx  # 0 for latest
    candle_dict = {
        f'candle_{candle_idx}_close_time': datetime.datetime.fromtimestamp(candle[6] / 1000).strftime(time_format),
        f'candle_{candle_idx}_update_time': fetch_time_str,
        f'candle_{candle_idx}_open_time': datetime.datetime.fromtimestamp(candle[0] / 1000).strftime(time_format),
        f'candle_{candle_idx}_close': str(candle[4]),
        f'candle_{candle_idx}_high': str(candle[2]),
        f'candle_{candle_idx}_open': str(candle[1]),
        f'candle_{candle_idx}_low': str(candle[3]),
    }
    new_candles.append(candle_dict)

# Load existing file if exists
if os.path.exists(output_path):
    with open(output_path, 'r') as f:
        existing_data = yaml.safe_load(f) or []
else:
    existing_data = []

# Ensure existing_data is a list
if not isinstance(existing_data, list):
    existing_data = []

# Merge: replace only the first N candles, keep the rest
for i in range(len(new_candles)):
    if i < len(existing_data):
        existing_data[i] = new_candles[i]  # Replace existing
    else:
        existing_data.append(new_candles[i])  # Append if missing

# Save back to file
with open(output_path, 'w') as f:
    yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)

# Execution time logging
exec_time = time.time() - start_time
current_time = datetime.datetime.now(datetime.UTC).strftime(time_format)
print(f"- - - - << {limit} >> candles << {interval} >> timeframe for << {symbol} >> at {current_time}")