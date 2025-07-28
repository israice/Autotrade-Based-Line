import yaml
import subprocess
import os

# Configuration file paths
C_TEMP_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
D_TEMP_OLD_CONFIG_PATH = "CORE/DATA/D_temp_old_config.yaml"
SELL_LONG_ORDER_PATH = "CORE/BACKEND/Y_MESSAGES/end_cross_green.py"
BUY_SHORT_ORDER_PATH = "CORE/BACKEND/Y_MESSAGES/end_cross_red.py"

# Variable names
SMALL_OPEN_STATUS = "SMALL_OPEN_STATUS"

# Expected values
GREEN_STATUS = "GREEN"
RED_STATUS = "RED"
CROSS_STATUS = "CROSS"

# Read YAML file
def read_yaml_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Get configuration values
try:
    c_temp_config = read_yaml_file(C_TEMP_CONFIG_PATH)
    d_temp_old_config = read_yaml_file(D_TEMP_OLD_CONFIG_PATH)

    # Extract SMALL_OPEN_STATUS from both configs
    c_status = c_temp_config.get(SMALL_OPEN_STATUS)
    d_status = d_temp_old_config.get(SMALL_OPEN_STATUS)

    # Check if values exist
    if c_status is None:
        raise KeyError(f"{SMALL_OPEN_STATUS} not found in {C_TEMP_CONFIG_PATH}")
    if d_status is None:
        raise KeyError(f"{SMALL_OPEN_STATUS} not found in {D_TEMP_OLD_CONFIG_PATH}")

    # Logic to run scripts based on conditions
    if c_status == GREEN_STATUS and d_status == CROSS_STATUS:
        if not os.path.exists(SELL_LONG_ORDER_PATH):
            raise FileNotFoundError(f"Script not found: {SELL_LONG_ORDER_PATH}")
        subprocess.run(["python", SELL_LONG_ORDER_PATH], check=True)
    elif c_status == RED_STATUS and d_status == CROSS_STATUS:
        if not os.path.exists(BUY_SHORT_ORDER_PATH):
            raise FileNotFoundError(f"Script not found: {BUY_SHORT_ORDER_PATH}")
        subprocess.run(["python", BUY_SHORT_ORDER_PATH], check=True)
    else:
        # Do nothing for any other case
        pass

except (FileNotFoundError, KeyError, subprocess.CalledProcessError) as e:
    print(f"Error: {str(e)}")
    exit(1)