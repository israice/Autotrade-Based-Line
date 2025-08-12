import os
import yaml
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
import decimal

# Configuration settings
ORDER_FILE = 'CORE/DATA/order_budy.yaml'
CANDLE_DATA_FILE = 'CORE/DATA/A_candle.yaml'
CORRECT_PRICE_KEY = 'candle_0_close'

# Load environment variables from .env file
load_dotenv()

# Read settings from order_budy.yaml
with open(ORDER_FILE, 'r') as file:
    data = yaml.safe_load(file)

ACCOUNT_ID = data['ORDER_ACCOUNT_ID']
SYMBOL = data['ORDER_SYMBOL']
LEVERAGE = data['ORDER_LEVERAGE']
MARGIN_USDT = data['ORDER_QUANTITY']
POSITION_SIDE = data['ORDER_POSITION_SIDE']
SIDE = data['ORDER_SIDE']
ORDER_TYPE = data['ORDER_TYPE']
STEP_SIZE = data['ORDER_STEP_SIZE']
MIN_QTY = data['ORDER_MIN_QTY']
MIN_NOTIONAL = data['ORDER_MIN_NOTIONAL']

# Добавлено: читаем цену для LIMIT ордера
ORDER_LIMIT_PRICE = data.get('ORDER_LIMIT_PRICE')

# Read candle data to get candle_0_close
with open(CANDLE_DATA_FILE, 'r') as file:
    candle_data = yaml.safe_load(file)
PRICE = candle_data[0][CORRECT_PRICE_KEY]

# Fetch API_KEY and API_SECRET from .env based on ACCOUNT_ID
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(f"API_KEY or API_SECRET not found for ACCOUNT_ID: {ACCOUNT_ID}")

client = Client(API_KEY, API_SECRET)

# Определяем цену для расчетов
# Для LIMIT ордеров используем ORDER_LIMIT_PRICE, для MARKET - текущую цену
if ORDER_TYPE == 'LIMIT':
    if ORDER_LIMIT_PRICE is None:
        raise ValueError("ORDER_LIMIT_PRICE must be specified for LIMIT orders")
    calculation_price = decimal.Decimal(str(ORDER_LIMIT_PRICE))
else:
    calculation_price = decimal.Decimal(str(PRICE))

# Calculate quantity for MARGIN_USDT at LEVERAGE (notional = MARGIN_USDT * LEVERAGE)
margin = decimal.Decimal(str(MARGIN_USDT))
leverage = decimal.Decimal(str(LEVERAGE))
notional = margin * leverage
quantity = notional / calculation_price

# Round down to nearest step size
dec_step = decimal.Decimal(str(STEP_SIZE))
quantity = (quantity // dec_step) * dec_step

# Convert to float for checks
float_quantity = float(quantity)
float_min_qty = float(decimal.Decimal(str(MIN_QTY)))

# Validate quantity
if float_quantity < float_min_qty:
    raise ValueError(f"Calculated quantity {float_quantity} is less than min_qty {float_min_qty}")

# Check minimum notional (используем цену для расчетов)
calc_notional = float_quantity * float(calculation_price)
float_min_notional = float(decimal.Decimal(str(MIN_NOTIONAL)))
if calc_notional < float_min_notional:
    raise ValueError(f"Calculated notional {calc_notional} is less than min_notional {float_min_notional}")

# Подготавливаем параметры ордера
order_params = {
    'symbol': SYMBOL,
    'side': SIDE,
    'positionSide': POSITION_SIDE,
    'type': ORDER_TYPE,
    'quantity': float_quantity
}

# Добавляем цену только для LIMIT ордеров
if ORDER_TYPE == 'LIMIT':
    order_params['price'] = float(ORDER_LIMIT_PRICE)
    order_params['timeInForce'] = 'GTC'  # Good Till Cancelled - стандарт для LIMIT ордеров

# Place the order
order = client.futures_create_order(**order_params)

# print(f"Order placed successfully: {order}")