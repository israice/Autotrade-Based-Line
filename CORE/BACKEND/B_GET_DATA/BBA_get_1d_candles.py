import sys
sys.dont_write_bytecode = True
import yaml
import platform  # Workaround for Windows freeze
import aiohttp
import asyncio
from datetime import datetime

# ================= НАСТРОЙКИ =================
SETTINGS_PATH = 'settings.yaml'  # Путь к файлу настроек
OUTPUT_PATH = 'CORE/DATA/A_fetch_candles.yaml'  # Путь к выходному YAML-файлу

def load_settings(path=SETTINGS_PATH):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

settings = load_settings()
symbol = settings['symbol'].upper()
interval = settings['buy_interval']
exchange = settings['exchange'].lower()
market_type = settings['market_type'].upper()
candles_limit = settings['candles_limit']
# =============================================

async def get_binance_futures_kline(session, symbol, interval, limit):
    url = 'https://fapi.binance.com/fapi/v1/klines'
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()

from datetime import datetime, timezone

def ms_to_readable(ts):
    # Convert milliseconds timestamp to ISO 8601 string, timezone-aware
    return datetime.fromtimestamp(int(ts) // 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

async def main():
    if exchange != 'binance' or market_type != 'PERPETUAL':
        print('Only Binance Perpetual is supported in this script.')
        sys.exit(1)

    try:
        async with aiohttp.ClientSession() as session:
            candles = await get_binance_futures_kline(session, symbol, interval, limit=candles_limit)
            candles = candles[::-1]  # candle_0 — самая свежая свеча
            columns = [
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            readable_candles = []
            for i, candle in enumerate(candles):
                candle_dict = {f"candle_{i}_" + col: val for col, val in zip(columns, candle)}
                # Replace times with readable format
                candle_dict[f"candle_{i}_open_time"] = ms_to_readable(candle_dict[f"candle_{i}_open_time"])
                candle_dict[f"candle_{i}_close_time"] = ms_to_readable(candle_dict[f"candle_{i}_close_time"])
                readable_candles.append(candle_dict)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(readable_candles, f, allow_unicode=True, sort_keys=False)
    except aiohttp.ClientResponseError as e:
        print(f"HTTP error: {e}\nResponse: {e.message}")
        sys.exit(1)

import signal

async def shutdown(loop, signal=None):
    if signal:
        print(f"\nReceived exit signal {signal.name}... Shutting down gracefully.")
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    signals = (signal.SIGINT, signal.SIGTERM) if hasattr(signal, 'SIGTERM') else (signal.SIGINT,)
    for s in signals:
        try:
            loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s)))
        except NotImplementedError:
            # Windows compatibility: add_signal_handler may not be implemented
            pass
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        loop.close()
