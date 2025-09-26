import yaml
import requests
import datetime
import time
import socket  # Added for error checking

# Settings
settings_path = 'settings.yaml'
output_path = 'CORE/DATA/AA_CANDLE.yaml'
api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'
time_format = '%Y-%m-%d %H:%M:%S'
symbol_key = 'symbol'
interval_key = 'timeframe_interval'
limit = 2
max_retries = 3  # Configurable retry count

# Load settings
with open(settings_path, 'r') as f:
    settings = yaml.safe_load(f)

symbol = settings[symbol_key]
interval = settings[interval_key]

# Logic starts here
start_time = time.time()

params = {
    'symbol': symbol,
    'interval': interval,
    'limit': limit
}

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

data = []
for idx in range(len(candles) - 1, -1, -1):  # Reverse to have latest first
    candle = candles[idx]
    candle_idx = len(candles) - 1 - idx  # 0 for latest, increasing for older
    candle_dict = {
        f'candle_{candle_idx}_close_time': datetime.datetime.fromtimestamp(candle[6] / 1000).strftime(time_format),
        f'candle_{candle_idx}_update_time': fetch_time_str,
        f'candle_{candle_idx}_open_time': datetime.datetime.fromtimestamp(candle[0] / 1000).strftime(time_format),
        f'candle_{candle_idx}_close': str(candle[4]),
        f'candle_{candle_idx}_high': str(candle[2]),
        f'candle_{candle_idx}_open': str(candle[1]),
        f'candle_{candle_idx}_low': str(candle[3]),
    }
    data.append(candle_dict)

with open(output_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

exec_time = time.time() - start_time
current_time = datetime.datetime.now(datetime.UTC).strftime(time_format)
print(f"- - - - << {limit} >> candles << {interval} >> timeframe for << {symbol} >> at {current_time}")