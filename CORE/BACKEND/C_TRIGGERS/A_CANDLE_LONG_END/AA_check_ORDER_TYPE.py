import yaml
import subprocess
import time
import os

# ###############################
CONFIG_HEADER = 'ORDER_TYPE_OF_LONG_END'
CONFIG_PATH = 'CORE/DATA/system_config.yaml'
SCRIPTS_UP_WORD = 'line'
SCRIPTS_DOWN_WORD = 'market'
# ###############################
SCRIPTS_UP = [
    'CORE/BACKEND/Z_TOOLS/message_ping.py',
]

SCRIPTS_DOWN = [
    # 'CORE/BACKEND/Z_TOOLS/order_buy_long.py',
    'CORE/BACKEND/Z_TOOLS/message_pong.py',
]
# ###############################

# Read config file
try:
    with open(CONFIG_PATH, 'r') as file:
        config = yaml.safe_load(file)
        type_candle = config.get(CONFIG_HEADER)
except FileNotFoundError:
    print(f"Error: Config file {CONFIG_PATH} not found")
    exit(1)
except yaml.YAMLError as e:
    print(f"Error: Failed to parse {CONFIG_PATH}: {e}")
    exit(1)

if type_candle is None:
    print(f"Error: {CONFIG_HEADER} not found in {CONFIG_PATH}")
    exit(1)

# Convert boolean to string if necessary
if isinstance(type_candle, bool):
    type_candle = SCRIPTS_UP_WORD if type_candle else SCRIPTS_DOWN_WORD

# Select script list based on config value
if type_candle == SCRIPTS_UP_WORD:
    scripts = SCRIPTS_UP
elif type_candle == SCRIPTS_DOWN_WORD:
    scripts = SCRIPTS_DOWN
else:
    print(f"Error: Invalid {CONFIG_HEADER} value: {type_candle}. Expected {SCRIPTS_UP_WORD} or {SCRIPTS_DOWN_WORD}")
    exit(1)

# Measure execution time and run scripts
start_time = time.time()
for script in scripts:
    if not os.path.exists(script):
        print(f"Error: Script {script} not found")
        continue
    try:
        result = subprocess.run(['python', script], capture_output=True, text=True)
        print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='')
    except subprocess.SubprocessError as e:
        print(f"Error executing {script}: {e}")
end_time = time.time()

# Print execution time
# print(f"Total execution time: {end_time - start_time:.2f} seconds")