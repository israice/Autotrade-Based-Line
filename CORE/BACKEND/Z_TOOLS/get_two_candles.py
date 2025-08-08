import yaml
import requests
import datetime
import time

# Settings
settings_path = 'CORE/DATA/user_settings.yaml'
output_path = 'CORE/DATA/A_candle.yaml'
api_base_url = 'https://fapi.binance.com'
api_endpoint = '/fapi/v1/klines'
time_format = '%Y-%m-%d %H:%M:%S'
symbol_key = 'symbol'
interval_key = 'timeframe_interval'
limit = 2

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

response = requests.get(f"{api_base_url}{api_endpoint}", params=params)
response.raise_for_status()
candles = response.json()

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