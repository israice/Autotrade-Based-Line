import os
import yaml
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from decimal import Decimal

# Файлы
ORDER_FILE = 'CORE/DATA/DD_ORDER_BODY.yaml'
CANDLE_DATA_FILE = 'CORE/DATA/AA_CANDLE.yaml'

# Имя ключа с ценой закрытия в YAML
CORRECT_PRICE_KEY = 'CLOSE_PRICE'

load_dotenv()

# Настройки ордера
with open(ORDER_FILE, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

ACCOUNT_ID     = cfg['ORDER_ACCOUNT_ID']
SYMBOL         = cfg['ORDER_SYMBOL']          # например: TAGUSDT
TIMEFRAME      = cfg.get('ORDER_TIMEFRAME', '1m')
LEVERAGE       = cfg['ORDER_LEVERAGE']
MARGIN_USDT    = cfg['ORDER_QUANTITY']
POSITION_SIDE  = cfg['ORDER_POSITION_SIDE']
SIDE           = cfg['ORDER_SIDE']
ORDER_TYPE     = cfg['ORDER_TYPE']
STEP_SIZE      = cfg['ORDER_STEP_SIZE']
MIN_QTY        = cfg['ORDER_MIN_QTY']
MIN_NOTIONAL   = cfg['ORDER_MIN_NOTIONAL']

# Читаем CLOSE_PRICE из CORE/DATA/AA_CANDLE.yaml
with open(CANDLE_DATA_FILE, 'r', encoding='utf-8') as f:
    y = yaml.safe_load(f)

try:
    # y['BINANCE_FUTURES'] -> список словарей вида {'TAGUSDT': [ {'1m': [ { ...candle... } ]} ]}
    bf = y['BINANCE_FUTURES']
    market = next(item for item in bf if SYMBOL in item)
    tf_wrappers = market[SYMBOL]                            # список словарей с таймфреймами
    tf_block = next(d[TIMEFRAME] for d in tf_wrappers if TIMEFRAME in d)  # список свечей
    candle = next((c for c in tf_block if c.get('CANDLE') == 0), tf_block[0])
    PRICE = Decimal(str(candle[CORRECT_PRICE_KEY]))
except (KeyError, IndexError, StopIteration, TypeError) as e:
    raise KeyError(f'Не удалось прочитать {CORRECT_PRICE_KEY} для {SYMBOL}/{TIMEFRAME} из {CANDLE_DATA_FILE}: {e}')

# Ключи API
API_KEY = os.getenv(f'{ACCOUNT_ID}_API_KEY')
API_SECRET = os.getenv(f'{ACCOUNT_ID}_API_SECRET')
if not API_KEY or not API_SECRET:
    raise ValueError(f'API_KEY или API_SECRET не найдены для ACCOUNT_ID: {ACCOUNT_ID}')

client = Client(API_KEY, API_SECRET)

# Расчёт количества (нотионал = маржа * плечо)
margin   = Decimal(str(MARGIN_USDT))
leverage = Decimal(str(LEVERAGE))
notional = margin * leverage
quantity = notional / PRICE

# Округление вниз до шага
step = Decimal(str(STEP_SIZE))
quantity = (quantity // step) * step

float_quantity   = float(quantity)
float_min_qty    = float(Decimal(str(MIN_QTY)))
float_min_notional = float(Decimal(str(MIN_NOTIONAL)))

# Валидации
if float_quantity < float_min_qty:
    raise ValueError(f'Рассчитанное количество {float_quantity} меньше min_qty {float_min_qty}')

calc_notional = float_quantity * float(PRICE)
if calc_notional < float_min_notional:
    raise ValueError(f'Рассчитанный нотионал {calc_notional} меньше min_notional {float_min_notional}')

# Отправка ордера
order = client.futures_create_order(
    symbol=SYMBOL,
    side=SIDE,
    positionSide=POSITION_SIDE,
    type=ORDER_TYPE,
    quantity=float_quantity
)
