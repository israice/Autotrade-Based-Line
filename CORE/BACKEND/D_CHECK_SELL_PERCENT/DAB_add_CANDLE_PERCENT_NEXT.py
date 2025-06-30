import re

SETTINGS_PATH = "settings.yaml"
TRADE_CONFIG_PATH = "CORE/DATA/B_trade_config.yaml"

# 1. Получить значение SELL_ON_PERCENT_CHANGE из settings.yaml
def get_sell_on_percent_change(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('SELL_ON_PERCENT_CHANGE:'):
                # Получить только число (или строку после ':')
                return line.split(':', 1)[1].strip().split()[0]
    raise ValueError('SELL_ON_PERCENT_CHANGE not found in settings.yaml')

# 2. Обновить только NEXT_LONG_PERCENT в B_trade_config.yaml

def update_NEXT_LONG_PERCENT(trade_config_path, add_value):
    with open(trade_config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    pattern = re.compile(r'^(NEXT_LONG_PERCENT:)\s*(.*)$')
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
            # Записываем всегда с тремя знаками после точки
            new_value_str = f"{new_value:.3f}"
            lines[i] = f'{indent}{prefix} {new_value_str}\n'
            break
    else:
        raise ValueError('NEXT_LONG_PERCENT not found in B_trade_config.yaml')
    with open(trade_config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def update_NEXT_SHORT_PERCENT(trade_config_path, new_value):
    with open(trade_config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    pattern = re.compile(r'^(NEXT_SHORT_PERCENT:)\s*.*$')
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = line.split(':', 1)[0]
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = f'{indent}{prefix}: {new_value}\n'
            break
    else:
        raise ValueError('NEXT_SHORT_PERCENT not found in B_trade_config.yaml')
    with open(trade_config_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    new_value = get_sell_on_percent_change(SETTINGS_PATH)
    update_NEXT_LONG_PERCENT(TRADE_CONFIG_PATH, new_value)
    # Присваиваем отрицательное значение для SHORT
    # Формируем отрицательное значение с сохранением формата (без .0 для целых)
    try:
        if isinstance(new_value, str):
            if '.' in new_value:
                negative_value = f'-{new_value.lstrip("-")}'
            else:
                negative_value = f'-{int(new_value.lstrip("-"))}'
        else:
            if float(new_value).is_integer():
                negative_value = f'-{int(abs(float(new_value)))}'
            else:
                negative_value = f'-{abs(float(new_value))}'
    except Exception:
        negative_value = f'-{str(new_value).lstrip("-")}'
    update_NEXT_SHORT_PERCENT(TRADE_CONFIG_PATH, negative_value)
