import sys
sys.dont_write_bytecode = True
import yaml
import aiohttp
import asyncio
from datetime import datetime

def load_settings(path='settings.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

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
    settings = load_settings()
    symbol = settings['symbol'].upper()
    interval = settings['interval']
    exchange = settings['exchange'].lower()
    market_type = settings['market_type'].upper()
    candles_limit = settings['candles_limit']

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
            with open('CHECK_CHANGE/AA_fetch_candles.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(readable_candles, f, allow_unicode=True, sort_keys=False)
    except aiohttp.ClientResponseError as e:
        print(f"HTTP error: {e}\nResponse: {e.message}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        print("Async task was cancelled at top-level.")
