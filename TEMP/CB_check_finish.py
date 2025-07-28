# проверяем закончилась ли свеча

import yaml
import subprocess

# Пути к файлам
file_new = 'CORE/DATA/A_small_new_candles_data.yaml'
file_old = 'CORE/DATA/E_small_old_candles_data.yaml'

# Список скриптов для запуска
scripts = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/CBA_check_trend.py',
]

def get_candle_open_time(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        # data должен быть списком словарей, ищем ключ candle_1_open_time
        for item in data:
            if 'candle_1_open_time' in item:
                return item['candle_1_open_time']
    return None

def main():
    open_time_new = get_candle_open_time(file_new)
    open_time_old = get_candle_open_time(file_old)

    # Если хотя бы одно значение None — просто завершить работу
    if open_time_new is None or open_time_old is None:
        return
    if open_time_new != open_time_old:
        for script in scripts:
            subprocess.run(['python', script], check=True)

if __name__ == '__main__':
    main()