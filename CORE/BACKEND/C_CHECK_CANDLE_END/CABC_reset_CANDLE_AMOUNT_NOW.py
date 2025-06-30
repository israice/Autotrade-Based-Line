import re

SETTINGS_PATH = r"c:/0_PROJECTS/05-PIEHOOK-based_line/settings.yaml"
TRADE_CONFIG_PATH = r"c:/0_PROJECTS/05-PIEHOOK-based_line/CORE/DATA/B_trade_config.yaml"

# 1. Получить значение START_AMOUNT из settings.yaml
def get_sell_on_percent_change(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('START_AMOUNT:'):
                # Получить только число (или строку после ':')
                return line.split(':', 1)[1].strip().split()[0]
    raise ValueError('START_AMOUNT not found in settings.yaml')

# 2. Обновить только CANDLE_AMOUNT_NOW в B_trade_config.yaml

def update_candle_percent_now(trade_config_path, new_value):
    with open(trade_config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    pattern = re.compile(r'^(CANDLE_AMOUNT_NOW:)\s*.*$')
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = line.split(':', 1)[0]
            # Сохраняем отступы
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = f'{indent}{prefix}: {new_value}\n'
            break
    else:
        raise ValueError('CANDLE_AMOUNT_NOW not found in B_trade_config.yaml')
    with open(trade_config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    new_value = get_sell_on_percent_change(SETTINGS_PATH)
    update_candle_percent_now(TRADE_CONFIG_PATH, new_value)
