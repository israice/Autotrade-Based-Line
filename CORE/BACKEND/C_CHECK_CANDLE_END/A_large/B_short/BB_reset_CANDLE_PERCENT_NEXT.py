import re

# ==== НАСТРОЙКИ ====
SETTINGS_PATH = "settings.yaml"
TRADE_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
SELL_ON_PERCENT_CHANGE_KEY = 'SELL_ON_PERCENT_CHANGE:'
NEXT_LONG_PERCENT_KEY = 'NEXT_LONG_PERCENT:'
NEXT_SHORT_PERCENT_KEY = 'NEXT_SHORT_PERCENT:'
YAML_ENCODING = 'utf-8'

# ==== ОСНОВНОЙ КОД ====
import re

def get_sell_on_percent_change(settings_path):
    with open(settings_path, 'r', encoding=YAML_ENCODING) as f:
        for line in f:
            if line.strip().startswith(SELL_ON_PERCENT_CHANGE_KEY):
                return line.split(':', 1)[1].strip().split()[0]
    raise ValueError(f'{SELL_ON_PERCENT_CHANGE_KEY} not found in {settings_path}')

def update_NEXT_LONG_PERCENT(trade_config_path, new_value):
    with open(trade_config_path, 'r', encoding=YAML_ENCODING) as f:
        lines = f.readlines()
    pattern = re.compile(rf'^({NEXT_LONG_PERCENT_KEY})\s*.*$')
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = line.split(':', 1)[0]
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = f'{indent}{prefix}: {new_value}\n'
            break
    else:
        raise ValueError(f'{NEXT_LONG_PERCENT_KEY} not found in {trade_config_path}')
    with open(trade_config_path, 'w', encoding=YAML_ENCODING) as f:
        f.writelines(lines)

def update_NEXT_SHORT_PERCENT(trade_config_path, new_value):
    with open(trade_config_path, 'r', encoding=YAML_ENCODING) as f:
        lines = f.readlines()
    pattern = re.compile(rf'^({NEXT_SHORT_PERCENT_KEY})\s*.*$')
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = line.split(':', 1)[0]
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = f'{indent}{prefix}: {new_value}\n'
            break
    else:
        raise ValueError(f'{NEXT_SHORT_PERCENT_KEY} not found in {trade_config_path}')
    with open(trade_config_path, 'w', encoding=YAML_ENCODING) as f:
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

print("- - C - - Candles percent reset successfully.")
