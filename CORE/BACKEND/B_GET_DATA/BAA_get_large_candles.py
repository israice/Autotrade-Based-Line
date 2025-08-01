import yaml
import requests
import time
from datetime import datetime
import os

# Settings
SETTINGS_FILE = 'settings.yaml'
OUTPUT_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
BINANCE_API_URL = 'https://fapi.binance.com/fapi/v1/klines'

# Supported Binance intervals
VALID_INTERVALS = [
    '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h',
    '1d', '3d', '1w', '1M'
]

def load_settings(file_path):
    """Load settings from YAML file."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return None

def validate_interval(interval):
    """Validate if the interval is supported by Binance."""
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval: {interval}. Supported intervals: {VALID_INTERVALS}")
    return interval

def fetch_klines(symbol, interval, limit):
    """Fetch klines data from Binance API."""
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
        print(f"Error fetching klines: {e}")
        return None

def format_timestamp(timestamp_ms):
    """Convert millisecond timestamp to formatted datetime string."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def save_candles_to_yaml(candles, output_file):
    """Save candles data to YAML file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    formatted_candles = []
    for i, candle in enumerate(reversed(candles)):
        formatted_candles.append({
            f'candle_{i}_open_time': format_timestamp(candle[0]),
            f'candle_{i}_open': str(candle[1]),
            f'candle_{i}_high': str(candle[2]),
            f'candle_{i}_low': str(candle[3]),
            f'candle_{i}_close': str(candle[4]),
            f'candle_{i}_volume': str(candle[5]),
            f'candle_{i}_close_time': format_timestamp(candle[6])
        })
    
    try:
        with open(output_file, 'w') as file:
            yaml.safe_dump(formatted_candles, file, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving to YAML: {e}")
        return False

def main():
    """Main function to execute the script."""
    start_time = time.time()
    
    # Load settings
    settings = load_settings(SETTINGS_FILE)
    if not settings:
        return
    
    symbol = settings.get('symbol')
    interval = settings.get('sell_interval')
    limit = settings.get('candles_limit')
    
    # Validate inputs
    try:
        validate_interval(interval)
        limit = int(limit)
        if limit <= 0:
            raise ValueError("Limit must be positive")
    except ValueError as e:
        print(f"Validation error: {e}")
        return
    
    # Fetch klines
    candles = fetch_klines(symbol, interval, limit)
    if not candles:
        return
    
    # Save to YAML
    if save_candles_to_yaml(candles, OUTPUT_FILE):
        execution_time = time.time() - start_time
        current_time = datetime.now().strftime('%H:%M:%S:%f')[:-3]
        print(f"- - B - - << {limit} >> candles << {interval} >> timeframe for << {symbol} >> at {current_time}")
        # print(f"{execution_time:.3f}s")

if __name__ == '__main__':
    main()