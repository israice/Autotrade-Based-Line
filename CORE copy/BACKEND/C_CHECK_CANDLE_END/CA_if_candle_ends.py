import yaml
from contextlib import redirect_stdout
import io
import os

# #############################
# check if candle ended       #
# by checking candle OPEN_TIME#
# #############################

# Settings
YAML_GROUP_INDEX = 0  # 0-based index of the YAML group to check
A_CANDLE_PATH = 'CORE/DATA/A_candle.yaml'
CLOSE_TIME_KEY = 'OPEN_TIME'  # for A_candle
COMPARISON_OPERATOR = '=='  # Supports '==', '!=', '>', '<', '>=', '<='
OPEN_TIME_KEY = 'OPEN_TIME'   # for Z_candle
Z_CANDLE_PATH = 'CORE/DATA/Z_candle.yaml'


SCRIPTS_EQUAL = [
]
SCRIPTS_NOT_EQUAL = [
    "CORE/BACKEND/C_CHECK_CANDLE_END/CAA_check_green_or_red.py",
]
SCRIPTS_NOT_FOUND = [
]

# Initialize variables
close_time = None
open_time = None

# Load YAML data for A
try:
    with open(A_CANDLE_PATH, 'r') as f:
        a_data = yaml.safe_load(f)
        if a_data is None:
            raise ValueError("YAML data is None")
        a_group = list(a_data.values())[YAML_GROUP_INDEX]
        if CLOSE_TIME_KEY not in a_group:
            raise KeyError(f"{CLOSE_TIME_KEY} not found in {A_CANDLE_PATH}")
        close_time = a_group[CLOSE_TIME_KEY]
except (FileNotFoundError, IndexError, TypeError, ValueError, KeyError):
    close_time = None

# Load YAML data for Z
try:
    with open(Z_CANDLE_PATH, 'r') as f:
        z_data = yaml.safe_load(f)
        if z_data is None:
            raise ValueError("YAML data is None")
        z_group = list(z_data.values())[YAML_GROUP_INDEX]
        if OPEN_TIME_KEY not in z_group:
            raise KeyError(f"{OPEN_TIME_KEY} not found in {Z_CANDLE_PATH}")
        open_time = z_group[OPEN_TIME_KEY]
except (FileNotFoundError, IndexError, TypeError, ValueError, KeyError):
    open_time = None

# Decide which scripts to run
if close_time is None or open_time is None:
    scripts_to_run = SCRIPTS_NOT_FOUND
else:
    if COMPARISON_OPERATOR == '==':
        condition = close_time == open_time
    elif COMPARISON_OPERATOR == '!=':
        condition = close_time != open_time
    elif COMPARISON_OPERATOR == '>':
        condition = close_time > open_time
    elif COMPARISON_OPERATOR == '<':
        condition = close_time < open_time
    elif COMPARISON_OPERATOR == '>=':
        condition = close_time >= open_time
    elif COMPARISON_OPERATOR == '<=':
        condition = close_time <= open_time
    else:
        raise ValueError(f"Unsupported comparison operator: {COMPARISON_OPERATOR}")

    scripts_to_run = SCRIPTS_EQUAL if condition else SCRIPTS_NOT_EQUAL

# Execute each script in order, capturing output
for script_path in scripts_to_run:
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        continue
    with open(script_path, 'r') as f:
        code = f.read()
    output_capture = io.StringIO()
    with redirect_stdout(output_capture):
        exec(code)
    output = output_capture.getvalue()
    if output.strip():  # Only print if output is not empty
        print(output.strip())
