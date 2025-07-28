import yaml
import subprocess
import os

# Configuration settings
C_TEMP_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
D_TEMP_OLD_CONFIG_PATH = "CORE/DATA/D_temp_old_config.yaml"
SELL_LONG_SCRIPT_PATH = "CORE/BACKEND/Y_MESSAGES/start_cross_green.py"
BUY_SHORT_SCRIPT_PATH = "CORE/BACKEND/Y_MESSAGES/start_cross_red.py"
LARGE_OPEN_STATUS_KEY = "LARGE_OPEN_STATUS"
GREEN_STATUS = "GREEN"
RED_STATUS = "RED"

def load_yaml_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    # Load configuration files
    c_config = load_yaml_file(C_TEMP_CONFIG_PATH)
    d_config = load_yaml_file(D_TEMP_OLD_CONFIG_PATH)

    # Check if LARGE_OPEN_STATUS exists in both configs
    if LARGE_OPEN_STATUS_KEY not in c_config:
        raise KeyError(f"{LARGE_OPEN_STATUS_KEY} not found in {C_TEMP_CONFIG_PATH}")
    if LARGE_OPEN_STATUS_KEY not in d_config:
        raise KeyError(f"{LARGE_OPEN_STATUS_KEY} not found in {D_TEMP_OLD_CONFIG_PATH}")

    # Get status values
    c_status = c_config[LARGE_OPEN_STATUS_KEY]
    d_status = d_config[LARGE_OPEN_STATUS_KEY]

    # Check conditions and run appropriate script
    if c_status == GREEN_STATUS and d_status == RED_STATUS:
        if not os.path.exists(SELL_LONG_SCRIPT_PATH):
            raise FileNotFoundError(f"Script {SELL_LONG_SCRIPT_PATH} not found")
        subprocess.run(["python", SELL_LONG_SCRIPT_PATH], check=True)
    elif c_status == RED_STATUS and d_status == GREEN_STATUS:
        if not os.path.exists(BUY_SHORT_SCRIPT_PATH):
            raise FileNotFoundError(f"Script {BUY_SHORT_SCRIPT_PATH} not found")
        subprocess.run(["python", BUY_SHORT_SCRIPT_PATH], check=True)
    # Do nothing in any other case

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")