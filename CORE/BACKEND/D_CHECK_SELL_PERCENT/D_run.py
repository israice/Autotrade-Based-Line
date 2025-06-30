import yaml
import subprocess
import os

# Корень проекта
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

# Путь к конфигу
CONFIG_PATH = os.path.join(project_root, 'CORE', 'DATA', 'B_trade_config.yaml')

# Скрипты для запуска (пути будут формироваться динамически)
SCRIPTS_LONG = [
    'CORE/BACKEND/D_CHECK_SELL_PERCENT/DA_SELL_LONG.py',
]
SCRIPTS_SHORT = [
    'CORE/BACKEND/D_CHECK_SELL_PERCENT/DB_SELL_SHORT.py',
]


def read_config(path):
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data

def parse_percent(val):
    if isinstance(val, str) and val.endswith('%'):
        return float(val.replace('%', '').replace(',', '.'))
    return float(val)

def run_scripts(scripts):
    for script in scripts:
        script_path = os.path.join(project_root, script)
        if os.path.isfile(script_path):
            subprocess.run(['python', script_path], check=False)
        else:
            print(f"[WARNING] Script not found: {script}")

def main():
    config = read_config(CONFIG_PATH)
    percent_change = parse_percent(config.get('PERCENTAGE_CHANGE'))
    next_long = float(config.get('NEXT_LONG_PERCENT'))
    next_short = float(config.get('NEXT_SHORT_PERCENT'))

    # Проверка условий
    if percent_change > next_long:
        run_scripts(SCRIPTS_LONG)
    elif percent_change < next_short:
        run_scripts(SCRIPTS_SHORT)

if __name__ == '__main__':
    main()
