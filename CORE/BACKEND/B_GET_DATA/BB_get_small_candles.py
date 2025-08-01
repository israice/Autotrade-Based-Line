import yaml
import requests
import time
from datetime import datetime
import os

# Settings
SETTINGS_FILE = 'settings.yaml'
OUTPUT_FILE = 'CORE/DATA/A_small_new_candles_data.yaml'
BINANCE_API_URL = 'https://fapi.binance.com/fapi/v1/klines'

# Load settings from YAML file
def load_settings():
    with open(SETTINGS_FILE, 'r') as file:
        return yaml.safe_load(file)

# Convert timestamp to formatted datetime string
def timestamp_to_datetime(timestamp_ms):
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

# Fetch candles from Binance API
def fetch_candles(symbol, interval, limit):
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(BINANCE_API_URL, params=params)
    response.raise_for_status()
    return response.json()

# Save candles to YAML file
def save_candles_to_yaml(candles):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    formatted_candles = []
    for i, candle in enumerate(reversed(candles)):  # Reverse to have newest candle as candle_0
        formatted_candles.append({
            f'candle_{i}_open_time': timestamp_to_datetime(candle[0]),
            f'candle_{i}_open': str(candle[1]),
            f'candle_{i}_high': str(candle[2]),
            f'candle_{i}_low': str(candle[3]),
            f'candle_{i}_close': str(candle[4]),
            f'candle_{i}_volume': str(candle[5]),
            f'candle_{i}_close_time': timestamp_to_datetime(candle[6])
        })
    with open(OUTPUT_FILE, 'w') as file:
        yaml.safe_dump(formatted_candles, file, sort_keys=False)

# Main execution
def main():
    start_time = time.time()
    
    # Load settings
    settings = load_settings()
    symbol = settings['symbol']
    interval = settings['buy_interval']
    limit = settings['candles_limit']
    
    # Fetch and save candles
    candles = fetch_candles(symbol, interval, limit)
    save_candles_to_yaml(candles)
    
    # Calculate execution time and display result
    end_time = time.time()
    execution_time = end_time - start_time
    current_time = datetime.now().strftime('%H:%M:%S:%f')[:-3]
    print(f"- - B - - << {limit} >> candles << {interval} >> timeframe for << {symbol} >> at {current_time}")
    # print(f"{execution_time:.3f}s")

if __name__ == '__main__':
    main()