import re

SETTINGS_PATH = "settings.yaml"
TRADE_CONFIG_PATH = "CORE/DATA/B_trade_config.yaml"

# 1. Получить значение START_AMOUNT из settings.yaml
def get_sell_on_percent_change(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('START_AMOUNT:'):
                # Получить только число (или строку после ':')
                return line.split(':', 1)[1].strip().split()[0]
    raise ValueError('START_AMOUNT not found in settings.yaml')

# 2. Обновить только STEP_AMOUNT_NOW в B_trade_config.yaml

def update_NEXT_LONG_PERCENT(trade_config_path, add_value):
    with open(trade_config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    pattern = re.compile(r'^(STEP_AMOUNT_NOW:)\s*(.*)$')
    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            prefix = match.group(1)
            current_value_str = match.group(2)
            indent = re.match(r'^(\s*)', line).group(1)
            try:
                current_value = float(current_value_str)
            except ValueError:
                current_value = 0.0
            try:
                add_value_num = float(add_value)
            except ValueError:
                add_value_num = 0.0
            new_value = current_value + add_value_num
            if new_value.is_integer():
                new_value_str = str(int(new_value))
            else:
                new_value_str = f'{new_value:.2f}'
            lines[i] = f'{indent}{prefix} {new_value_str}\n'
            break
    else:
        raise ValueError('STEP_AMOUNT_NOW not found in B_trade_config.yaml')
    with open(trade_config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    new_value = get_sell_on_percent_change(SETTINGS_PATH)
    update_NEXT_LONG_PERCENT(TRADE_CONFIG_PATH, new_value)
