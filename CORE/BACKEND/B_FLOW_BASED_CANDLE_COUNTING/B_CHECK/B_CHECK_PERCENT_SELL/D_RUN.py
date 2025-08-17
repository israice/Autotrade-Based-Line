import yaml
import os
import sys
import time

CONFIG_PATH = 'CORE/DATA/CC_TRIGGERS_CONFIG.yaml'
CONFIG_HEADER = 'FLOW_1'
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_DOWN_WORD = 'DISABLE'

SCRIPTS_YES = [
    "CORE/BACKEND/D_CHECK_PERCENT_SELL/DA_if_percent_positive_or_negative.py", 
]

SCRIPTS_NO = [
]

config_value = None
try:
    with open(CONFIG_PATH, 'r') as file:
        config = yaml.safe_load(file)
        if config is not None:
            config_value = config.get(CONFIG_HEADER)
except FileNotFoundError:
    pass
except yaml.YAMLError as e:
    pass

if config_value is None:
    scripts = []
else:
    if isinstance(config_value, bool):
        config_value = SCRIPTS_UP_WORD if config_value else SCRIPTS_DOWN_WORD

    if config_value == SCRIPTS_UP_WORD:
        scripts = SCRIPTS_YES
    elif config_value == SCRIPTS_DOWN_WORD:
        scripts = SCRIPTS_NO
    else:
        print(f" - Wrong value key {config_value} for {CONFIG_HEADER}")
        sys.exit(1)

start_time = time.time()

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
        
        exec(code, exec_globals)
    except Exception as e:
        print(f"Error executing {script}: {e}")

end_time = time.time()
execution_time = end_time - start_time
formatted_time = f"{execution_time:.3f}"
# if formatted_time != "0.000":
#     print(f"- Execution time: {formatted_time} seconds ✔️")