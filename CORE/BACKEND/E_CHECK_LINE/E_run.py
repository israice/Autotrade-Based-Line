
# ================= ЧТО ДЕЛАЕТ СКРИПТ =================
# проверяет TREND_LARGE: RED или TREND_LARGE: GREEN
# в итоге запускает список RED или список GREEN
# =====================================================

import yaml
import subprocess
import os

# Определяем корень проекта по расположению .env
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
config_path = os.path.join(project_root, 'CORE', 'DATA', 'C_temp_config.yaml')

def norm_path(rel_path):
    """
    Преобразует путь с прямыми слэшами (относительно корня проекта) в абсолютный путь
    """
    return os.path.abspath(os.path.join(project_root, rel_path))

# Теперь можно указывать пути относительно корня проекта
GREEN_SCRIPT = norm_path(
    'CORE/BACKEND/E_CHECK_LINE/EA_BUY_LONG.py',
    )
RED_SCRIPT = norm_path(
    'CORE/BACKEND/E_CHECK_LINE/EB_BUY_SHORT.py',
    )

def get_trend(cfg_path):
    with open(cfg_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('TREND_LARGE', '').strip().upper()

def main():
    trend = get_trend(config_path)
    if trend == 'GREEN':
        subprocess.run(['python', GREEN_SCRIPT], check=True)
    elif trend == 'RED':
        subprocess.run(['python', RED_SCRIPT], check=True)
    else:
        print(f'Неизвестное значение TREND_LARGE: {trend}')

if __name__ == '__main__':
    main()
