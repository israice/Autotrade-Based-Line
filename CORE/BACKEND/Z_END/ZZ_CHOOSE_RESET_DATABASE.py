import yaml
import os
import io
import contextlib
import sys

CONFIG_PATH = 'CORE/DATA/user_settings.yaml'
CONFIG_HEADER = 'RESET_DATABASE'
SCRIPTS_UP_WORD = 'YES'
SCRIPTS_DOWN_WORD = 'NO'

SCRIPTS_YES = [
    "TOOLS/COPY_CANDLES.py",
]
SCRIPTS_NO = [
    "TOOLS/COPY_CANDLES.py",
]

try:
    with open(CONFIG_PATH, 'r') as file:
        config = yaml.safe_load(file)
        config_value = config.get(CONFIG_HEADER)
except FileNotFoundError:
    print(f"Error: Config file {CONFIG_PATH} not found")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error: Failed to parse {CONFIG_PATH}: {e}")
    sys.exit(1)

if config_value is None:
    print(f"Error: {CONFIG_HEADER} not found in {CONFIG_PATH}")
    sys.exit(1)

if isinstance(config_value, bool):
    config_value = SCRIPTS_UP_WORD if config_value else SCRIPTS_DOWN_WORD

if config_value == SCRIPTS_UP_WORD:
    scripts = SCRIPTS_YES
elif config_value == SCRIPTS_DOWN_WORD:
    scripts = SCRIPTS_NO
else:
    print(f" - Wrong value key {config_value} for {CONFIG_HEADER}")
    sys.exit(1)

for script in scripts:
    if not os.path.exists(script):
        print(f"Error: Script {script} not found")
        continue
    try:
        # Читаем код скрипта
        with open(script, 'r') as f:
            code = compile(f.read(), script, 'exec')
        
        # Подготавливаем окружение для exec (мимикрируем __main__)
        exec_globals = {'__name__': '__main__', '__file__': script}
        
        # Захватываем вывод
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(code, exec_globals)
        
        # Выводим captured output
        print(output.getvalue(), end='')
    except Exception as e:
        print(f"Error executing {script}: {e}")