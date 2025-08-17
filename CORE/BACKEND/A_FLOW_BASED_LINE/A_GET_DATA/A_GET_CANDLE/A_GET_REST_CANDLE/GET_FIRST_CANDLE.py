import websocket
import json
import yaml
import sys
import signal
from datetime import datetime, timezone
import threading
import time

# Load user settings
with open('CORE/DATA/BB_USER_SETTINGS.yaml', 'r') as f:
    settings = yaml.safe_load(f)

# All settings defined here
WS_URL = "wss://fstream.binance.com/stream"
FILE_PATH = "CORE/DATA/AA_CANDLE.yaml"
WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
SUBSCRIBE_PARAMS = [f"{symbol.lower()}@kline_{WEBSOCKET_TIMEFRAME}" for symbol in WEBSOCKET_SYMBOL]

# Global variables
candles = {}
interrupted = False

# Logic functions
def on_open(ws):
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": SUBSCRIBE_PARAMS,
        "id": 1
    }
    ws.send(json.dumps(subscribe_message))

def on_message(ws, message):
    data = json.loads(message)
    if 'data' in data and 'k' in data['data']:
        k = data['data']['k']
        symbol = data['data']['s']
        key = f"{symbol}_{WEBSOCKET_TIMEFRAME}"
        open_time_str = datetime.fromtimestamp(k['t']/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:000')
        close_time_str = datetime.fromtimestamp(k['T']/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:999')
        timestamp_str = datetime.fromtimestamp(data['data']['E']/1000, timezone.utc).strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]
        candles[key] = {
            'CLOSE_TIME': close_time_str,
            'TIMESTAMP': timestamp_str,
            'OPEN_TIME': open_time_str,
            'HIGH_PRICE': float(k['h']),
            'CLOSE_PRICE': float(k['c']),
            'OPEN_PRICE': float(k['o']),
            'LOW_PRICE': float(k['l'])
        }
        with open(FILE_PATH, 'w') as f:
            yaml.dump(candles, f, sort_keys=False)
        # Check if we have candles for all symbols
        if len(candles) == len(WEBSOCKET_SYMBOL):
            ws.close()

def on_error(ws, error):
    if not isinstance(error, KeyboardInterrupt):
        pass

def on_close(ws, close_status_code, close_msg):
    pass

def signal_handler(sig, frame):
    global interrupted
    print("Interrupted, closing WebSocket...")
    ws.close()
    interrupted = True

# Run the script
signal.signal(signal.SIGINT, signal_handler)
websocket.enableTrace(False)
ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
ws.run_forever()
if interrupted:
    sys.exit(0)