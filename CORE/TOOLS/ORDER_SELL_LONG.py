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


def abs_qty_str(s) -> str:
    """
    Возвращает модуль числа в виде строки без знака.
    Подходит для Decimal, int, float и str.
    """
    d = Decimal(str(s))
    d = abs(d).normalize()
    # Убираем возможный научный формат вида '1E-8'
    return format(d, 'f').rstrip('0').rstrip('.') if '.' in format(d, 'f') else format(d, 'f')


def build_market_order(symbol, side, qty_str, position_side=None, use_reduce_only=False):
    """
    Конструирует маркет-ордер для фьючерсов.
    """
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

    # Если в ответе есть строки с positionSide=LONG/SHORT, значит hedge-режим.
    has_long_short_rows = any(p.get('positionSide') in ('LONG', 'SHORT') for p in positions)

    orders = []

    if has_long_short_rows:
        # --- HEDGE MODE: закрываем ТОЛЬКО LONG без reduceOnly ---
        long_amt = Decimal('0')

        for p in positions:
            if p.get('positionSide') == 'LONG':
                amt = Decimal(p.get('positionAmt', '0'))
                if amt != 0:
                    long_amt = abs(amt)
                    break

        if long_amt > 0:
            orders.append(
                build_market_order(
                    symbol=symbol,
                    side="SELL",
                    qty_str=abs_qty_str(long_amt),
                    position_side="LONG",
                    use_reduce_only=False
                )
            )

    else:
        # --- ONE-WAY MODE: одна запись BOTH; ТОЛЬКО если amt > 0 (LONG) ---
        if positions:
            p = positions[0]
            amt = Decimal(p.get('positionAmt', '0'))
            if amt > 0:
                orders.append(
                    build_market_order(
                        symbol=symbol,
                        side="SELL",
                        qty_str=abs_qty_str(amt),
                        position_side=None,
                        use_reduce_only=True  # важно, чтобы не открыть шорт
                    )
                )
            # Если amt < 0 (шорт) — НИЧЕГО не делаем.

    # Нет LONG-позиций для закрытия — выходим молча (это не ошибка)
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
