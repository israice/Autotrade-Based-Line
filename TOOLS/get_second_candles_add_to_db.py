import requests
import json
import yaml
import sys
from datetime import datetime, timezone
import csv
import os
from collections import OrderedDict

# Load settings from YAML file
with open('CORE/DATA/user_settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)
WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
CANDLE_NUMBER = 1
# Define all possible timeframes in the desired order
timeframes = [WEBSOCKET_TIMEFRAME]
tf_order = {tf: idx for idx, tf in enumerate(timeframes)}
# Settings
FILE_PATH = "CORE\\DATA\\Y_database.csv"
candles = {}
expected_len = len(WEBSOCKET_SYMBOL) * len(timeframes)
if __name__ == "__main__":
    for symbol in WEBSOCKET_SYMBOL:
        for tf in timeframes:
            url = "https://fapi.binance.com/fapi/v1/klines"
            params = {
                "symbol": symbol,
                "interval": tf,
                "limit": CANDLE_NUMBER + 1
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                klines = response.json()
                if len(klines) > CANDLE_NUMBER:
                    candle = klines[-(CANDLE_NUMBER + 1)]
                    key = f"{symbol}_{tf}"
                    open_time_str = datetime.fromtimestamp(candle[0]/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:000')
                    close_time_str = datetime.fromtimestamp(candle[6]/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:999')
                    timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]
                    candles[key] = {
                        'CLOSE_TIME': close_time_str,
                        'TIMESTAMP': timestamp_str,
                        'OPEN_TIME': open_time_str,
                        'HIGH_PRICE': float(candle[2]),
                        'CLOSE_PRICE': float(candle[4]),
                        'OPEN_PRICE': float(candle[1]),
                        'LOW_PRICE': float(candle[3])
                    }
                else:
                    print(f"Not enough historical data for {symbol} {tf} at index {CANDLE_NUMBER}")
            else:
                print(f"Error fetching data for {symbol} {tf}: {response.status_code} - {response.text}")
    if candles:
        symbol_rows = OrderedDict()
        header = ['TIMEFRAME', 'CANDLE_NUMBER', 'SYMBOL', 'HIGH_PRICE', 'CLOSE_PRICE', 'OPEN_PRICE', 'LOW_PRICE', 'CLOSE_TIME', 'TIMESTAMP', 'OPEN_TIME']
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r', newline='') as f:
                reader = csv.reader(f)
                try:
                    next(reader)  # skip header
                except StopIteration:
                    pass
                for row in reader:
                    if row:
                        symbol = row[2]
                        if symbol not in symbol_rows:
                            symbol_rows[symbol] = []
                        symbol_rows[symbol].append(row)
        # Add new candles
        sorted_keys = sorted(candles.keys(), key=lambda k: (k.split('_')[0], tf_order.get(k.split('_')[1], len(timeframes))))
        for key in sorted_keys:
            symbol, tf = key.split('_')
            candle_data = candles[key]
            new_row = [tf, '1', symbol, candle_data['HIGH_PRICE'], candle_data['CLOSE_PRICE'], candle_data['OPEN_PRICE'], candle_data['LOW_PRICE'], candle_data['CLOSE_TIME'], candle_data['TIMESTAMP'], candle_data['OPEN_TIME']]
            if symbol in symbol_rows:
                for old_row in symbol_rows[symbol]:
                    old_candle_num = int(old_row[1])
                    old_row[1] = str(old_candle_num + 1)
                symbol_rows[symbol].insert(0, new_row)
            else:
                symbol_rows[symbol] = [new_row]
        # Write back to file
        with open(FILE_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for sym, rows in symbol_rows.items():
                for row in rows:
                    writer.writerow(row)
    else:
        print("No candles data retrieved.")

