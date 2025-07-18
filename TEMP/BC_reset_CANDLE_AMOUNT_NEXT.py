import re

# ==== НАСТРОЙКИ ====
SETTINGS_PATH = "settings.yaml"
TRADE_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
START_AMOUNT_KEY = 'START_AMOUNT:'
STEP_AMOUNT_NOW_KEY = 'STEP_AMOUNT_NOW:'
YAML_ENCODING = 'utf-8'

# ==== ОСНОВНОЙ КОД ====
import re

def get_sell_on_percent_change(settings_path):
    with open(settings_path, 'r', encoding=YAML_ENCODING) as f:
        for line in f:
            if line.strip().startswith(START_AMOUNT_KEY):
                return line.split(':', 1)[1].strip().split()[0]
    raise ValueError(f'{START_AMOUNT_KEY} not found in {settings_path}')

def update_NEXT_LONG_PERCENT(trade_config_path, new_value):
    with open(trade_config_path, 'r', encoding=YAML_ENCODING) as f:
        lines = f.readlines()
    pattern = re.compile(rf'^({STEP_AMOUNT_NOW_KEY})\s*.*$')
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            prefix = line.split(':', 1)[0]
            indent = re.match(r'^(\s*)', line).group(1)
            lines[i] = f'{indent}{prefix}: {new_value}\n'
            break
    else:
        raise ValueError(f'{STEP_AMOUNT_NOW_KEY} not found in {trade_config_path}')
    with open(trade_config_path, 'w', encoding=YAML_ENCODING) as f:
        f.writelines(lines)

if __name__ == "__main__":
    new_value = get_sell_on_percent_change(SETTINGS_PATH)
    update_NEXT_LONG_PERCENT(TRADE_CONFIG_PATH, new_value)

print("- - C - - Candles amount reset successfully.")
