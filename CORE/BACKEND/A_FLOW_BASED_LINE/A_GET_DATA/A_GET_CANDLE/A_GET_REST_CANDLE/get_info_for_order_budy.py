import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
from ruamel.yaml import YAML

# Configuration settings
SETTINGS_FILE = 'CORE/DATA/BB_USER_SETTINGS.yaml'
SYMBOL_KEY = 'symbol'
ACCOUNT_ID_KEY = 'ACCOUNT_ID'
# Parameter keys for output
OUTPUT_FILE = 'CORE/DATA/DD_ORDER_BODY.yaml'
MIN_QTY_KEY = 'ORDER_MIN_QTY'
STEP_SIZE_KEY = 'ORDER_STEP_SIZE'
MIN_NOTIONAL_KEY = 'ORDER_MIN_NOTIONAL'
ORDER_LEVERAGE_KEY = 'ORDER_LEVERAGE'  # Added key for leverage

# Load environment variables from .env file
load_dotenv()

# Read settings from BB_USER_SETTINGS.yaml
yaml = YAML()
yaml.preserve_quotes = False  # Disable preserving quotes in output
yaml.default_flow_style = False  # Use block style for readability
try:
    with open(SETTINGS_FILE, 'r') as file:
        settings = yaml.load(file)
    ACCOUNT_ID = settings[ACCOUNT_ID_KEY]
    SYMBOL = settings[SYMBOL_KEY]
except FileNotFoundError:
    raise FileNotFoundError(f"Settings file not found: {SETTINGS_FILE}")
except KeyError as e:
    raise KeyError(f"Missing key in BB_USER_SETTINGS.yaml: {e}")

# Fetch API_KEY and API_SECRET from .env based on ACCOUNT_ID
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(f"API_KEY or API_SECRET not found for ACCOUNT_ID: {ACCOUNT_ID}")

# Initialize Binance client
client = Client(API_KEY, API_SECRET)

# Fetch symbol info for futures market
try:
    futures_info = client.futures_exchange_info()['symbols']
    symbol_info = next((s for s in futures_info if s['symbol'] == SYMBOL), None)
    if not symbol_info:
        raise ValueError(f"No symbol info found for {SYMBOL} in futures market.")
except Exception as e:
    raise ValueError(f"Failed to fetch futures symbol info for {SYMBOL}: {e}")

# Extract parameters and convert to float to avoid quotes in YAML
new_params = {}
filters = symbol_info.get('filters', [])

for f in filters:
    if f['filterType'] == 'LOT_SIZE':
        new_params[MIN_QTY_KEY] = float(f['minQty'])
        new_params[STEP_SIZE_KEY] = float(f['stepSize'])
    if f['filterType'] == 'MIN_NOTIONAL':
        new_params[MIN_NOTIONAL_KEY] = float(f.get('notional', '0'))

# Ensure required parameters are found
if not all(key in new_params for key in [MIN_QTY_KEY, STEP_SIZE_KEY, MIN_NOTIONAL_KEY]):
    missing = [key for key in [MIN_QTY_KEY, STEP_SIZE_KEY, MIN_NOTIONAL_KEY] if key not in new_params]
    raise ValueError(f"Could not retrieve parameters {missing} for {SYMBOL}")

# Fetch max leverage for the symbol
try:
    leverage_bracket = client.futures_leverage_bracket(symbol=SYMBOL)
    max_leverage = int(leverage_bracket[0]['brackets'][0]['initialLeverage'])
except Exception as e:
    raise ValueError(f"Failed to fetch max leverage for {SYMBOL}: {e}")

# Check and set margin type to ISOLATED and leverage to max if necessary
try:
    position_info = client.futures_position_information(symbol=SYMBOL)
except BinanceAPIException as e:
    print(f"Failed to get position information for {SYMBOL}: {e}")
    position_info = []

current_margin_type = 'unknown'
current_leverage = 0

if position_info:
    info = position_info[0]
    current_margin_type = info.get('marginType', 'cross').lower()
    current_leverage = int(info.get('leverage', 0))

# Set margin type if necessary
if current_margin_type != 'isolated':
    try:
        client.futures_change_margin_type(symbol=SYMBOL, marginType='ISOLATED')
        print(f"Changed margin type to <<< ISOLATED >>> for {SYMBOL}")
    except BinanceAPIException as e:
        if e.code == -4046:
            print(f"- - - Margin type already <<< ISOLATED >>> for {SYMBOL}")
        else:
            print(f"Error changing margin type for {SYMBOL}: {e}. This may occur if there are open positions/orders.")

# Set leverage if necessary (after ensuring isolated mode)
if current_margin_type == 'isolated' or 'already' in locals().get('margin_change_msg', ''):  # Rough check if set succeeded
    if current_leverage != max_leverage:
        try:
            client.futures_change_leverage(symbol=SYMBOL, leverage=max_leverage)
            print(f"Changed leverage to <<< {max_leverage} >>> for {SYMBOL}.")
        except BinanceAPIException as e:
            if e.code == -4047:
                print(f"Leverage already {max_leverage} for {SYMBOL} (no change needed).")
            else:
                print(f"Error changing leverage for {SYMBOL}: {e}. This may occur if there are open positions/orders or invalid leverage.")
else:
    # If no position info or unknown, attempt to set
    try:
        client.futures_change_leverage(symbol=SYMBOL, leverage=max_leverage)
        print(f"- - - Set leverage to <<< {max_leverage} >>> for {SYMBOL}")
    except BinanceAPIException as e:
        if e.code == -4047:
            print(f"Leverage already {max_leverage} for {SYMBOL} (no prior info).")
        else:
            print(f"Error setting leverage for {SYMBOL}: {e}.")

# Read existing YAML file (if it exists) with comments preserved
existing_params = {}
try:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as file:
            existing_params = yaml.load(file) or {}
except Exception as e:
    print(f"Warning: Could not read existing {OUTPUT_FILE}: {e}. Starting with empty params.")

# Update only the specified keys with plain float values
existing_params.update({
    MIN_QTY_KEY: new_params[MIN_QTY_KEY],
    STEP_SIZE_KEY: new_params[STEP_SIZE_KEY],
    MIN_NOTIONAL_KEY: new_params[MIN_NOTIONAL_KEY],
    ORDER_LEVERAGE_KEY: max_leverage  # Added update for leverage
})

# Save updated parameters to YAML file, preserving comments
try:
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as file:
        yaml.dump(existing_params, file)
except Exception as e:
    raise IOError(f"Failed to write to {OUTPUT_FILE}: {e}")