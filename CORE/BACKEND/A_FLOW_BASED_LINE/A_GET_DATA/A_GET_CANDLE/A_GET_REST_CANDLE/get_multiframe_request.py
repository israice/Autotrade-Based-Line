import websocket
import json
import yaml
import sys
import signal
from datetime import datetime, timezone

# Load settings from YAML file
with open('CORE/DATA/BB_USER_SETTINGS.yaml', 'r') as f:
    settings = yaml.safe_load(f)

WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']

# Define all possible timeframes in the desired order
timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
tf_order = {tf: idx for idx, tf in enumerate(timeframes)}

# Settings
SUBSCRIBE_PARAMS = [f"{symbol.lower()}@kline_{tf}" for symbol in WEBSOCKET_SYMBOL for tf in timeframes]
WS_URL = "wss://fstream.binance.com/stream"
FILE_PATH = "CORE\\DATA\\AA_CANDLE.yaml"

candles = {}
received = set()
expected_len = len(WEBSOCKET_SYMBOL) * len(timeframes)

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
        tf = k['i']
        key = f"{symbol}_{tf}"
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
        if key not in received:
            received.add(key)
            if len(received) == expected_len:
                # Sort the keys: first by symbol, then by timeframe order
                sorted_keys = sorted(candles.keys(), key=lambda k: (k.split('_')[0], tf_order.get(k.split('_')[1], len(timeframes))))
                ordered_candles = {k: candles[k] for k in sorted_keys}
                with open(FILE_PATH, 'w') as f:
                    yaml.dump(ordered_candles, f, sort_keys=False)
                ws.close()

def on_error(ws, error):
    if not isinstance(error, KeyboardInterrupt):
        pass

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def signal_handler(sig, frame):
    print("Interrupted, closing WebSocket...")
    ws.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()