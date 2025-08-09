import os
import yaml
from dotenv import load_dotenv
from binance.client import Client

# Configuration settings
ORDER_FILE = 'CORE/DATA/order_budy.yaml'

# Load environment variables from .env file
load_dotenv()

# Read settings from order_budy.yaml
with open(ORDER_FILE, 'r') as file:
    data = yaml.safe_load(file)

ACCOUNT_ID = data['ORDER_ACCOUNT_ID']
SYMBOL = data['ORDER_SYMBOL']

# Fetch API_KEY and API_SECRET from .env based on ACCOUNT_ID
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError(f"API_KEY or API_SECRET not found for ACCOUNT_ID: {ACCOUNT_ID}")

client = Client(API_KEY, API_SECRET)

# Отменяем все ордера для символа одним запросом
try:
    result = client.futures_cancel_all_open_orders(symbol=SYMBOL)
    print(f"✓ Все ордера для пары {SYMBOL} успешно отменены")
    # print(f"Результат: {result}")
except Exception as e:
    print(f"✗ Ошибка при отмене ордеров: {e}")