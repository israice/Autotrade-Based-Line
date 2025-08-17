import yaml
import os
import io
import contextlib
import sys
import time

# ################################### #
# check if allowed to run config list #
# ################################### #

CONFIG_PATH = 'CORE/DATA/CC_TRIGGERS_CONFIG.yaml'
CONFIG_HEADER = 'RUN_BEFORE_START'
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_DOWN_WORD = 'DISABLE'

SCRIPTS_YES = [
    # ########### RESET DB ##################
    "CORE/TOOLS_FLOW/RESET_DB.py",
    "CORE/TOOLS_FLOW/GET_CANDLE_1_ADD_TO_DB.py",
    "CORE/TOOLS_FLOW/GET_CANDLE_2_ADD_TO_DB.py",
    "CORE/TOOLS_FLOW/RESET_CANDLE_DATA_FILES.py",
    # #######################################
    # "TOOLS/create_ORDER_SYMBOL.py", 
    # "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    # "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    # "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    # "TOOLS/reset_PERCENT_SELL.py",
    # "TOOLS/reset_TREND_STATUS.py",
    # "TOOLS/enable_CROSSING_UP_GREEN.py",
    # "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    # "TOOLS/disable_CROSSING_UP_RED.py",
    # "TOOLS/enable_CROSSING_DOWN_RED.py",
    # "TOOLS/create_ORDER_ACCOUNT_ID.py",
    # 'TOOLS/binance_info_for_order_budy.py',
    # 'TOOLS/clone_candles.py',
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
        
        # Захватываем вывод
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(code, exec_globals)
        
        # Выводим captured output
        print(output.getvalue(), end='')
    except Exception as e:
        print(f"Error executing {script}: {e}")

end_time = time.time()
execution_time = end_time - start_time
formatted_time = f"{execution_time:.3f}"
# if formatted_time != "0.000":
#     print(f"- Execution time: {formatted_time} seconds ✔️")