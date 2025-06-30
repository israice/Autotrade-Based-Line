# Скрипт для сброса значения CANDLE_PERCENT_NOW в 0 в файле B_trade_config.yaml
# Не изменяет порядок и формат остальных строк.

import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'DATA', 'B_trade_config.yaml')
CONFIG_PATH = os.path.abspath(CONFIG_PATH)

KEY = 'CANDLE_PERCENT_NOW:'
NEW_VALUE = 'CANDLE_PERCENT_NOW: 0\n'

def reset_candle_percent_now():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.strip().startswith(KEY):
            lines[i] = NEW_VALUE
            break

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == '__main__':
    reset_candle_percent_now()
