import os
import yaml
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
import decimal

# Configuration settings
ORDER_FILE = 'CORE/DATA/order_budy.yaml'

# Load environment variables from .env file
load_dotenv()

# Read all settings from order_budy.yaml
with open(ORDER_FILE, 'r') as file:
    data = yaml.safe_load(file)

ACCOUNT_ID = data['ORDER_ACCOUNT_ID']
SYMBOL = data['ORDER_SYMBOL']
LEVERAGE = data['ORDER_LEVERAGE']
MARGIN_USDT = data['ORDER_MARGIN_USDT']
PRICE = data['ORDER_PRICE']
POSITION_SIDE = data['ORDER_POSITION_SIDE']
SIDE = data['ORDER_SIDE']
ORDER_TYPE = data['ORDER_TYPE']
STEP_SIZE = data['ORDER_STEP_SIZE']
MIN_QTY = data['ORDER_MIN_QTY']
MIN_NOTIONAL = data['ORDER_MIN_NOTIONAL']
QUANTITY = data['ORDER_QUANTITY']

# Fetch API_KEY and API_SECRET from .env based on ACCOUNT_ID
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(f"API_KEY or API_SECRET not found for ACCOUNT_ID: {ACCOUNT_ID}")

client = Client(API_KEY, API_SECRET)

# Use decimal for precise validation
price = decimal.Decimal(str(PRICE))
quantity = decimal.Decimal(str(QUANTITY))

# Convert to float for checks
float_quantity = float(quantity)
float_min_qty = float(decimal.Decimal(str(MIN_QTY)))

# Validate quantity
if float_quantity < float_min_qty:
    raise ValueError(f"Quantity {float_quantity} is less than min_qty {float_min_qty}")

# Check minimum notional
calc_notional = float_quantity * float(price)
float_min_notional = float(decimal.Decimal(str(MIN_NOTIONAL)))
if calc_notional < float_min_notional:
    raise ValueError(f"Calculated notional {calc_notional} is less than min_notional {float_min_notional}")

# Place the order
order = client.futures_create_order(
    symbol=SYMBOL,
    side=SIDE,
    positionSide=POSITION_SIDE,
    type=ORDER_TYPE,
    quantity=float_quantity
)