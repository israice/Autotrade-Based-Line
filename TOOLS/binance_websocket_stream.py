import websocket
import json
import yaml
import sys
import signal
from datetime import datetime, timezone
import threading
import time

# Settings
WS_URL = "wss://fstream.binance.com/stream"
FILE_PATH = "CORE/DATA/A_candle.yaml"

candles = {}
interrupted = False

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

def on_error(ws, error):
    if not isinstance(error, KeyboardInterrupt):
        pass

def on_close(ws, close_status_code, close_msg):
    print("WebSocket restarted or clossing by user")

def signal_handler(sig, frame):
    global interrupted
    print("Interrupted, closing WebSocket...")
    ws.close()
    interrupted = True

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        with open('CORE/DATA/user_settings.yaml', 'r') as f:
            settings = yaml.safe_load(f)
        WEBSOCKET_TIMEFRAME = settings['WEBSOCKET_TIMEFRAME']
        WEBSOCKET_SYMBOL = settings['WEBSOCKET_SYMBOL']
        WEBSOCKET_RESTART_INTERVAL = settings['WEBSOCKET_RESTART_INTERVAL']
        SUBSCRIBE_PARAMS = [f"{symbol.lower()}@kline_{WEBSOCKET_TIMEFRAME}" for symbol in WEBSOCKET_SYMBOL]
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        def restart_timer():
            time.sleep(WEBSOCKET_RESTART_INTERVAL * 60)
            ws.close()
        timer = threading.Thread(target=restart_timer)
        timer.daemon = True
        timer.start()
        ws.run_forever()
        if interrupted:
            break