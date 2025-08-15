import sys
from datetime import datetime, timezone, timedelta
import time
import requests
import csv
import os
import yaml

# Load user settings
with open('CORE/DATA/user_settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)

# All settings defined here
BASE_URLS = [
    "https://fapi.binance.com",
    "https://fapi1.binance.com",
    "https://fapi2.binance.com",
    "https://fapi3.binance.com"
]
FILE_PATH = "CORE/DATA/Y_database.csv"
WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
CANDLE_NUMBER = 1

# Helper function to parse time
def parse_time(time_str):
    if not time_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    base_str = time_str[:-4]
    ms_str = time_str[-3:]
    base = datetime.strptime(base_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    ms = int(ms_str)
    return base + timedelta(milliseconds=ms)

# Helper function to write to CSV
def write_to_csv(new_rows):
    fieldnames = ['TIMEFRAME', 'CANDLE_NUMBER', 'SYMBOL', 'HIGH_PRICE', 'CLOSE_PRICE', 'OPEN_PRICE', 'LOW_PRICE', 'CLOSE_TIME', 'TIMESTAMP', 'OPEN_TIME']
    
    all_rows = []
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            all_rows = [row for row in reader]
    
    all_rows.extend(new_rows)
    
    # Deduplicate by SYMBOL, TIMEFRAME, OPEN_TIME
    unique_keys = set()
    deduped_rows = []
    for row in all_rows:
        key = (row['SYMBOL'], row['TIMEFRAME'], row['OPEN_TIME'])
        if key not in unique_keys:
            unique_keys.add(key)
            deduped_rows.append(row)
    
    # Sort by SYMBOL, TIMEFRAME, OPEN_TIME
    deduped_rows.sort(key=lambda r: (r['SYMBOL'], r['TIMEFRAME'], parse_time(r['OPEN_TIME'])))
    
    # Assign CANDLE_NUMBER within each group
    prev_group = None
    current_number = 1
    for row in deduped_rows:
        group = (row['SYMBOL'], row['TIMEFRAME'])
        if group != prev_group:
            current_number = 1
            prev_group = group
        row['CANDLE_NUMBER'] = current_number
        current_number += 1
    
    # Write back
    with open(FILE_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduped_rows)

# Run the script
current_time = datetime.now(timezone.utc)
now_ms = time.time() * 1000
new_rows = []
for symbol in WEBSOCKET_SYMBOL:
    data = None
    for base in BASE_URLS:
        url = f"{base}/fapi/v1/klines?symbol={symbol}&interval={WEBSOCKET_TIMEFRAME}&limit={CANDLE_NUMBER + 10}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    break
        except Exception as e:
            print(f"Error with {base}: {e}")
    if data is None:
        print(f"Failed to fetch data for {symbol} from all sources")
        continue

    closed_klines = [k for k in data if k[6] < now_ms]
    if len(closed_klines) < CANDLE_NUMBER:
        print(f"Not enough closed candles for {symbol}")
        continue

    for i in range(CANDLE_NUMBER):
        kline = closed_klines[-(i + 1)]
        open_time = kline[0]
        open_price = float(kline[1])
        high_price = float(kline[2])
        low_price = float(kline[3])
        close_price = float(kline[4])
        close_time = kline[6]
        timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]
        open_time_str = datetime.fromtimestamp(open_time / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:000')
        close_time_str = datetime.fromtimestamp(close_time / 1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:999')
        row = {
            'TIMEFRAME': WEBSOCKET_TIMEFRAME,
            'CANDLE_NUMBER': 0,  # Will be set later
            'SYMBOL': symbol,
            'HIGH_PRICE': high_price,
            'CLOSE_PRICE': close_price,
            'OPEN_PRICE': open_price,
            'LOW_PRICE': low_price,
            'CLOSE_TIME': close_time_str,
            'TIMESTAMP': timestamp_str,
            'OPEN_TIME': open_time_str
        }
        new_rows.append(row)

write_to_csv(new_rows)