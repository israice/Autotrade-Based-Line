import yaml
import subprocess

# File paths
A_CANDLE_PATH = 'CORE/DATA/A_candle.yaml'
CANDLE_KEY = 'candle_0_open'
Z_CANDLE_PATH = 'CORE/DATA/Z_candle.yaml'

# Script lists
GREEN_LIST = [
    "TOOLS/message_candle_green_end.py",
    # "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    # "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    # "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    # "TOOLS/reset_PERCENT_SELL.py",
    # "TOOLS/reset_TREND_STATUS.py",
    # "TOOLS/enable_CROSSING_UP_GREEN.py",
    # "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    # "TOOLS/disable_CROSSING_UP_RED.py",
    # "TOOLS/enable_CROSSING_DOWN_RED.py",
    
]

RED_LIST = [
    "TOOLS/message_candle_red_end.py",
    "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    "TOOLS/reset_PERCENT_SELL.py",
    "TOOLS/reset_TREND_STATUS.py",
    "TOOLS/enable_CROSSING_UP_GREEN.py",
    "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    "TOOLS/disable_CROSSING_UP_RED.py",
    "TOOLS/enable_CROSSING_DOWN_RED.py",
    
]

GLOBAL_LIST = [
    "TOOLS/message_candle_started_with_same_open.py",
    "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    "TOOLS/reset_PERCENT_SELL.py",
    "TOOLS/reset_TREND_STATUS.py",
    "TOOLS/enable_CROSSING_UP_GREEN.py",
    "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    "TOOLS/disable_CROSSING_UP_RED.py",
    "TOOLS/enable_CROSSING_DOWN_RED.py",
]

def load_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def run_scripts(script_list):
    for script in script_list:
        subprocess.run(['python', script], check=True)

# Load the YAML files
a_candle = load_yaml_file(A_CANDLE_PATH)
z_candle = load_yaml_file(Z_CANDLE_PATH)

# Extract candle_0_open values from the first dictionary in the list
a_open = float(a_candle[0][CANDLE_KEY])
z_open = float(z_candle[0][CANDLE_KEY])

# Compare values and run appropriate scripts
if a_open > z_open:
    run_scripts(GREEN_LIST)
elif a_open < z_open:
    run_scripts(RED_LIST)
else:
    run_scripts(GLOBAL_LIST)