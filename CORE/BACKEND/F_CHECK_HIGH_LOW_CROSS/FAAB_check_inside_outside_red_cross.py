import yaml
import subprocess

# Variable names and paths
CANDLE_FILE_PATH = 'CORE/DATA/A_candle.yaml'
CANDLE_0_CLOSE_KEY = 'candle_0_close'
CANDLE_1_HIGH_KEY = 'candle_1_low'
GREEN_SCRIPT_PATHS = [
    "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FAABA_check_status_CROSSING_UP_RED.py",
]
RED_SCRIPT_PATHS = [
    "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FAABB_check_status_CROSSING_DOWN_RED.py",

]

def load_yaml_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None

def run_scripts(script_list):
    for script in script_list:
        try:
            subprocess.run(['python', script], check=True)
        except subprocess.CalledProcessError:
            pass  # Silently handle script execution errors

def main():
    # Load YAML data
    data = load_yaml_data(CANDLE_FILE_PATH)
    if not data:
        return

    # Extract candle values from the list of dictionaries
    try:
        candle_0_close = float(data[0][CANDLE_0_CLOSE_KEY])  # Access first candle (index 0)
        candle_1_high = float(data[1][CANDLE_1_HIGH_KEY])   # Access second candle (index 1)
    except (IndexError, KeyError, ValueError) as e:
        print(f"Error processing candle data: {e}")
        return

    # Compare and run appropriate scripts
    if candle_0_close > candle_1_high:
        run_scripts(GREEN_SCRIPT_PATHS)
    else:
        run_scripts(RED_SCRIPT_PATHS)

# Settings
SCRIPTS_GREEN = GREEN_SCRIPT_PATHS
SCRIPTS_RED = RED_SCRIPT_PATHS

if __name__ == "__main__":
    main()