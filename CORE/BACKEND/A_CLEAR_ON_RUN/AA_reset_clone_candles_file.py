import yaml

# Путь к YAML-файлу
yaml_path = "CORE/DATA/Z_clone_candles.yaml"

# Функция для рекурсивной замены всех значений на None
def replace_values_with_none(data):
    if isinstance(data, dict):
        return {k: replace_values_with_none(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_values_with_none(item) for item in data]
    else:
        return None

# Загрузка YAML-файла
with open(yaml_path, 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

# Замена всех значений на None
if isinstance(yaml_data, list):
    new_data = [replace_values_with_none(item) for item in yaml_data]
else:
    new_data = replace_values_with_none(yaml_data)

# Сохранение обратно в файл
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(new_data, f, allow_unicode=True, default_flow_style=False)
