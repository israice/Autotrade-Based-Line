import yaml
import os
yaml_path = 'CHECK_CHANGE/AB_check_trend.yaml'
yaml_path_0 = 'CHECK_CHANGE/AA_fetch_candles.yaml'
yaml_path_1 = 'CHECK_CHANGE/ZZ_clone_candles.yaml'

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

def write_percentage_and_trend(path, percent_value, trend_value=None):
    # Прочитать существующий YAML, если есть
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            pass
    data['PERCENTAGE_CHANGE'] = percent_value
    if trend_value is not None:
        data['TREND'] = trend_value
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

def main():
    # candle_0_close из первого элемента (индекс 0) файла AA_fetch_candles.yaml
    candle_0_close = read_close_from_yaml(yaml_path_0, 'candle_0_close', 0)
    # candle_1_close из второго элемента (индекс 1) файла ZZ_clone_candles.yaml
    candle_1_close = read_close_from_yaml(yaml_path_1, 'candle_1_close', 1)

    if candle_0_close is None or candle_1_close is None:
        print('Одна из необходимых переменных не найдена. Проверьте наличие файлов и ключей.')
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
    write_percentage_and_trend(yaml_path, percent_str, trend)

if __name__ == '__main__':
    main()
