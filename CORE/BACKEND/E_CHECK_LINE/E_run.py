
# ================= ЧТО ДЕЛАЕТ СКРИПТ =================
# проверяет TREND: RED или TREND: GREEN
# в итоге запускает список RED или список GREEN
# =====================================================

import yaml
import subprocess
import os

# Определяем корень проекта по расположению .env
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
env_path = os.path.join(project_root, '.env')
config_path = os.path.join(project_root, 'CORE', 'DATA', 'B_trade_config.yaml')

def norm_path(rel_path):
    """
    Преобразует путь с прямыми слэшами (относительно корня проекта) в абсолютный путь
    """
    return os.path.abspath(os.path.join(project_root, rel_path))

# Теперь можно указывать пути относительно корня проекта
GREEN_SCRIPT = norm_path(
    'CORE/BACKEND/E_CHECK_LINE/EAB_add_CANDLE_AMOUNT_NEXT.py',
    )
RED_SCRIPT = norm_path(
    'CORE/BACKEND/E_CHECK_LINE/EBB_add_CANDLE_AMOUNT_NEXT.py',
    )

def get_trend(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('TREND', '').strip().upper()

def main():
    trend = get_trend(config_path)
    if trend == 'GREEN':
        subprocess.run(['python', GREEN_SCRIPT], check=True)
    elif trend == 'RED':
        subprocess.run(['python', RED_SCRIPT], check=True)
    else:
        print(f'Неизвестное значение TREND: {trend}')

if __name__ == '__main__':
    main()
