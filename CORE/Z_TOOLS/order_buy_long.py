import os
import yaml
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
import decimal

# Configuration settings
SETTINGS_FILE = 'settings.yaml'
CONFIG_FILE = 'config.yaml'
CANDLE_DATA_FILE = 'CORE/B_GET_DATA/BA_get_large_candle.yaml'
ACCOUNT_ID_KEY = 'ACCOUNT_ID'
SYMBOL_KEY = 'symbol'
LEVERAGE_KEY = 'COIN_LEVERAGE'
MARGIN_KEY = 'NOW_AMOUNT'
CANDLE_CLOSE_KEY = 'candle_0_close'
STEP_SIZE = '0.1'  # Lot size step size for XRPUSDT
MIN_QTY = '0.1'   # Minimum quantity for XRPUSDT
MIN_NOTIONAL = '5' # Minimum notional value in USDT
POSITION_SIDE = 'LONG'  # 'LONG' or 'SHORT'
ORDER_TYPE = 'MARKET'  # Order type, e.g., 'MARKET'

# Load environment variables from .env file
load_dotenv()

# Read settings from settings.yaml
with open(SETTINGS_FILE, 'r') as file:
    settings = yaml.safe_load(file)
ACCOUNT_ID = settings[ACCOUNT_ID_KEY]
SYMBOL = settings[SYMBOL_KEY]
LEVERAGE = settings[LEVERAGE_KEY]

# Fetch API_KEY and API_SECRET from .env based on ACCOUNT_ID
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(f"API_KEY or API_SECRET not found for ACCOUNT_ID: {ACCOUNT_ID}")

# Read config.yaml to get NOW_AMOUNT
with open(CONFIG_FILE, 'r') as file:
    config = yaml.safe_load(file)
MARGIN_USDT = config[MARGIN_KEY]

# Read candle data to get candle_0_close
with open(CANDLE_DATA_FILE, 'r') as file:
    candle_data = yaml.safe_load(file)
PRICE = candle_data[0][CANDLE_CLOSE_KEY]

# Derived side based on POSITION_SIDE
if POSITION_SIDE == 'LONG':
    SIDE = 'BUY'
elif POSITION_SIDE == 'SHORT':
    SIDE = 'SELL'
else:
    raise ValueError("POSITION_SIDE must be 'LONG' or 'SHORT'")

client = Client(API_KEY, API_SECRET)

# Calculate quantity for MARGIN_USDT at LEVERAGE (notional = MARGIN_USDT * LEVERAGE)
price = decimal.Decimal(str(PRICE))
margin = decimal.Decimal(str(MARGIN_USDT))
leverage = decimal.Decimal(str(LEVERAGE))
notional = margin * leverage
quantity = notional / price

# Round down to nearest step size
dec_step = decimal.Decimal(STEP_SIZE)
quantity = (quantity // dec_step) * dec_step

# Convert to float for checks
float_quantity = float(quantity)
float_min_qty = float(MIN_QTY)

# Validate quantity
if float_quantity < float_min_qty:
    raise ValueError(f"Calculated quantity {float_quantity} is less than min_qty {float_min_qty}")

# Check minimum notional
calc_notional = float_quantity * float(price)
if calc_notional < float(MIN_NOTIONAL):
    raise ValueError(f"Calculated notional {calc_notional} is less than min_notional {MIN_NOTIONAL}")

# Place the order
order = client.futures_create_order(
    symbol=SYMBOL,
    side=SIDE,
    positionSide=POSITION_SIDE,
    type=ORDER_TYPE,
    quantity=float_quantity
)