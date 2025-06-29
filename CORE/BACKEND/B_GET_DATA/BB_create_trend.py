import yaml
import os
import re

# ==== НАСТРОЙКИ (ТОЛЬКО ВВЕРХУ) ====
YAML_PATH_TREND = 'CORE/DATA/B_trade_config.yaml'
YAML_PATH_CANDLES_0 = 'CORE/DATA/A_fetch_candles.yaml'
YAML_PATH_CANDLES_1 = 'CORE/DATA/Z_clone_candles.yaml'
KEY_PERCENTAGE_CHANGE = 'PERCENTAGE_CHANGE'
KEY_TREND = 'TREND'
KEY_CANDLE_0_CLOSE = 'candle_0_close'
KEY_CANDLE_1_CLOSE = 'candle_1_close'
# ====================================

def read_close_from_yaml(path, key, index):
    if not os.path.exists(path):
        print(f"Файл не найден: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
        except Exception as e:
            print(f"Ошибка чтения YAML из {path}: {e}")
            return None
    if not isinstance(data, list):
        print(f"Ожидался список в файле {path}, но получено: {type(data)}")
        return None
    if len(data) <= index:
        print(f"В файле {path} недостаточно элементов для индекса {index}")
        return None
    if key not in data[index]:
        print(f"Ключ '{key}' не найден в элементе {index} файла {path}")
        return None
    return data[index][key]

import re

def update_yaml_values_preserve_order(filepath, updates):
    """
    updates: dict, например {'PERCENTAGE_CHANGE': '0.123', 'TREND': 'RED'}
    Меняет только значения переменных, порядок и формат сохраняется.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        for key, value in updates.items():
            # ищем строку вида KEY: ... (без учёта пробелов)
            if re.match(rf'^{re.escape(key)}\s*:', line):
                # заменяем только значение
                prefix = re.match(rf'^({re.escape(key)}\s*:\s*)', line)
                if prefix:
                    lines[i] = prefix.group(1) + str(value) + '\n'
                break

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def write_percentage_and_trend(path, percent_value, trend_value=None):
    # Только для YAML_PATH_TREND используем точечную замену
    if os.path.basename(path) == os.path.basename(YAML_PATH_TREND):
        updates = {KEY_PERCENTAGE_CHANGE: percent_value}
        if trend_value is not None:
            updates[KEY_TREND] = trend_value
        update_yaml_values_preserve_order(path, updates)
        return
    # Для других файлов — стандартная логика
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            pass
    data[KEY_PERCENTAGE_CHANGE] = percent_value
    if trend_value is not None:
        data[KEY_TREND] = trend_value
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

def main():
    # candle_0_close из первого элемента (индекс 0) файла YAML_PATH_CANDLES_0
    candle_0_close = read_close_from_yaml(YAML_PATH_CANDLES_0, KEY_CANDLE_0_CLOSE, 0)
    # candle_1_close из второго элемента (индекс 1) файла YAML_PATH_CANDLES_1
    candle_1_close = read_close_from_yaml(YAML_PATH_CANDLES_1, KEY_CANDLE_1_CLOSE, 1)

    if candle_0_close is None or candle_1_close is None:
        return

    try:
        c0 = float(candle_0_close)
        c1 = float(candle_1_close)
    except Exception as e:
        print(f'Ошибка преобразования значений к числу: {e}')
        return

    # Вычисляем процентное изменение относительно candle_1_close
    try:
        percent = ((c0 - c1) / abs(c1)) * 100 if c1 != 0 else 0
    except Exception as e:
        print(f'Ошибка вычисления процента: {e}')
        return
    percent_str = f'{percent:.3f}%'
    # Определяем TREND
    trend = None
    if percent > 0:
        trend = 'GREEN'
    elif percent < 0:
        trend = 'RED'
    # Если percent == 0, trend не меняем
    write_percentage_and_trend(YAML_PATH_TREND, percent_str, trend)

if __name__ == '__main__':
    main()
