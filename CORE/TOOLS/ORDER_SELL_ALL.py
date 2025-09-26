#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import yaml
from decimal import Decimal
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

ORDER_FILE = 'CORE/DATA/DD_ORDER_BODY.yaml'

def abs_qty_str(s: str) -> str:
    s = str(s)
    return s[1:] if s.startswith('-') else s

def build_market_order(symbol, side, qty_str, position_side=None, use_reduce_only=False):
    o = {
        "symbol": symbol,
        "side": side,                 # "BUY" / "SELL"
        "type": "MARKET",
        "quantity": qty_str,          # строкой!
        "newOrderRespType": "RESULT",
    }
    if position_side is not None:     # только в hedge-режиме
        o["positionSide"] = position_side  # "LONG" / "SHORT"
    if use_reduce_only:               # только в one-way
        o["reduceOnly"] = "true"
    return o

def main():
    load_dotenv()

    # --- читаем из YAML пару и ACCOUNT_ID, ключи — из окружения по ACCOUNT_ID ---
    try:
        with open(ORDER_FILE, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        account_id = str(cfg.get('ORDER_ACCOUNT_ID', '')).strip()
        symbol = str(cfg['ORDER_SYMBOL']).upper()
    except Exception as e:
        print(f"Ошибка чтения {ORDER_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    if not account_id:
        print("Ошибка: в YAML отсутствует ORDER_ACCOUNT_ID.", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv(f'{account_id}_API_KEY')
    api_secret = os.getenv(f'{account_id}_API_SECRET')
    if not api_key or not api_secret:
        print(f"Ошибка: переменные окружения {account_id}_API_KEY / {account_id}_API_SECRET не найдены.", file=sys.stderr)
        sys.exit(1)

    client = Client(api_key, api_secret)

    # --- читаем позиции по символу и определяем режим (hedge / one-way) ---
    try:
        positions = client.futures_position_information(symbol=symbol)
    except BinanceAPIException as e:
        print(f"Binance API error @position_information: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка @position_information: {e}", file=sys.stderr)
        sys.exit(1)

    has_long_short_rows = any(p.get('positionSide') in ('LONG', 'SHORT') for p in positions)

    orders = []

    if has_long_short_rows:
        # --- HEDGE MODE: закрываем обе стороны без reduceOnly ---
        long_amt = Decimal('0')
        short_amt = Decimal('0')

        for p in positions:
            side = p.get('positionSide')
            amt = Decimal(p.get('positionAmt', '0'))
            if side == 'LONG' and amt != 0:
                long_amt = abs(amt)
            elif side == 'SHORT' and amt != 0:
                short_amt = abs(amt)

        if long_amt > 0:
            orders.append(build_market_order(symbol, "SELL", abs_qty_str(long_amt), position_side="LONG", use_reduce_only=False))
        if short_amt > 0:
            orders.append(build_market_order(symbol, "BUY",  abs_qty_str(short_amt), position_side="SHORT", use_reduce_only=False))

    else:
        # --- ONE-WAY MODE: одна запись BOTH; reduceOnly=true, без positionSide ---
        if positions:
            p = positions[0]
            amt = Decimal(p.get('positionAmt', '0'))
            if amt > 0:
                orders.append(build_market_order(symbol, "SELL", abs_qty_str(amt), position_side=None, use_reduce_only=True))
            elif amt < 0:
                orders.append(build_market_order(symbol, "BUY",  abs_qty_str(amt), position_side=None, use_reduce_only=True))

    # Нет позиций для закрытия — выходим молча (это не ошибка)
    if not orders:
        return

    # --- один batch-запрос на закрытие ---
    try:
        client.futures_place_batch_order(batchOrders=orders)
    except BinanceAPIException as e:
        print(f"Binance API error @batch_order: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка @batch_order: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
