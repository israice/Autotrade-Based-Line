import os
import time
import yaml
import math

# Настройки
CORE_CONFIG_PATH = 'CORE/DATA/C_temp_config.yaml'
SETTINGS_PATH = 'settings.yaml'
LARGE_OPEN_CHANGE_KEY = 'LARGE_OPEN_CHANGE'
NEXT_LONG_PERCENT_KEY = 'NEXT_LONG_PERCENT'
SELL_ON_PERCENT_CHANGE_KEY = 'SELL_ON_PERCENT_CHANGE'

# Проверка существования файлов
if not os.path.exists(CORE_CONFIG_PATH):
    raise FileNotFoundError(f"File not found: {CORE_CONFIG_PATH}")
if not os.path.exists(SETTINGS_PATH):
    raise FileNotFoundError(f"File not found: {SETTINGS_PATH}")

start_time = time.time()

# Чтение settings.yaml
with open(SETTINGS_PATH, 'r') as f:
    settings_data = yaml.safe_load(f)

sell_on_percent_change = settings_data.get(SELL_ON_PERCENT_CHANGE_KEY)
if sell_on_percent_change is None:
    raise ValueError(f"Key not found: {SELL_ON_PERCENT_CHANGE_KEY} in {SETTINGS_PATH}")

# Чтение CORE/DATA/C_temp_config.yaml как текст для сохранения структуры
with open(CORE_CONFIG_PATH, 'r') as f:
    core_lines = f.readlines()

# Парсинг значений из core_config
core_data = yaml.safe_load(''.join(core_lines))

LARGE_OPEN_CHANGE = core_data.get(LARGE_OPEN_CHANGE_KEY)
next_long_percent = core_data.get(NEXT_LONG_PERCENT_KEY)

if LARGE_OPEN_CHANGE is None:
    raise ValueError(f"Key not found: {LARGE_OPEN_CHANGE_KEY} in {CORE_CONFIG_PATH}")
if next_long_percent is None:
    raise ValueError(f"Key not found: {NEXT_LONG_PERCENT_KEY} in {CORE_CONFIG_PATH}")

if LARGE_OPEN_CHANGE > next_long_percent:
    # Рассчет количества добавлений
    diff = LARGE_OPEN_CHANGE - next_long_percent
    additions_needed = math.ceil((diff + sell_on_percent_change) / sell_on_percent_change)
    addition_total = additions_needed * sell_on_percent_change
    new_next_long_percent = next_long_percent + addition_total
    # Форматирование до 3 знаков
    new_next_long_percent_str = f"{new_next_long_percent:.3f}"
else:
    new_next_long_percent_str = f"{next_long_percent:.3f}"

# Форматирование LARGE_OPEN_CHANGE до 3 знаков (всегда заменяем для consistency)
LARGE_OPEN_CHANGE_str = f"{LARGE_OPEN_CHANGE:.3f}"

# Замена в строках
updated_lines = []
for line in core_lines:
    if line.strip().startswith(LARGE_OPEN_CHANGE_KEY + ':'):
        updated_lines.append(f"{LARGE_OPEN_CHANGE_KEY}: {LARGE_OPEN_CHANGE_str}\n")
    elif line.strip().startswith(NEXT_LONG_PERCENT_KEY + ':'):
        updated_lines.append(f"{NEXT_LONG_PERCENT_KEY}: {new_next_long_percent_str}\n")
    else:
        updated_lines.append(line)

# Запись обратно
with open(CORE_CONFIG_PATH, 'w') as f:
    f.writelines(updated_lines)

end_time = time.time()
execution_time = end_time - start_time
# print(f"Script execution time: {execution_time:.2f} seconds")