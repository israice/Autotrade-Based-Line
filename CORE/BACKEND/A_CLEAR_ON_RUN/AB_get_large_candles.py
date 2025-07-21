import yaml
import requests
import time
from datetime import datetime
import os

# Configuration
SETTINGS_FILE = 'settings.yaml'
OUTPUT_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
BINANCE_API_URL = 'https://fapi.binance.com/fapi/v1/klines'

# Load settings from YAML file
with open(SETTINGS_FILE, 'r') as file:
    settings = yaml.safe_load(file)

SYMBOL = settings.get('symbol')
INTERVAL = settings.get('sell_interval')
LIMIT = settings.get('candles_limit')

def fetch_binance_candles(symbol, interval, limit):
    """Fetch candlestick data from Binance Futures API."""
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    
    try:
        response = requests.get(BINANCE_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def format_timestamp(ms):
    """Convert millisecond timestamp to formatted datetime string."""
    return datetime.fromtimestamp(ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def save_candles_to_yaml(candles):
    """Format and save candle data to YAML file."""
    formatted_data = []
    
    # Reverse candles to have newest first (candle_0 is current)
    for i, candle in enumerate(reversed(candles)):
        candle_data = {
            f'candle_{i}_open_time': format_timestamp(candle[0]),
            f'candle_{i}_open': str(candle[1]),
            f'candle_{i}_high': str(candle[2]),
            f'candle_{i}_low': str(candle[3]),
            f'candle_{i}_close': str(candle[4]),
            f'candle_{i}_volume': str(candle[5]),
            f'candle_{i}_close_time': format_timestamp(candle[6])
        }
        formatted_data.append(candle_data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Save to YAML file
    with open(OUTPUT_FILE, 'w') as file:
        yaml.dump(formatted_data, file, allow_unicode=True, sort_keys=False)

def main():
    """Main function to fetch and save candles."""
    start_time = time.time()
    
    candles = fetch_binance_candles(SYMBOL, INTERVAL, LIMIT)
    if candles:
        save_candles_to_yaml(candles)
    
    execution_time = time.time() - start_time
    print(f"- - A - - Successfully saved {LIMIT} candles for {SYMBOL} at {INTERVAL} interval")
    # print(f"Script execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()

