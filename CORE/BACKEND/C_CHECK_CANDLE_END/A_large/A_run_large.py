import yaml
import subprocess
import time
from pathlib import Path

# Configuration
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
TREND_KEY = "TREND_LARGE"
GREEN_VALUE = "GREEN"
RED_VALUE = "RED"

SCRIPTS_LONG = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_long/A_run.py',
]
SCRIPTS_SHORT = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/B_short/B_run.py',
]

# Functions
def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            try:
                result = subprocess.run(['python', str(script_path)], capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(result.stderr.strip())
            except Exception as e:
                print(f"Error running script {script}: {e}")
        else:
            print(f"Script {script} not found")
    end_time = time.time()
    # print(f"Total execution time: {end_time - start_time:.2f} seconds")

def main():
    config = load_config(CONFIG_FILE)
    if config and TREND_KEY in config:
        trend_value = config[TREND_KEY]
        if trend_value == GREEN_VALUE:
            run_scripts(SCRIPTS_LONG)
        elif trend_value == RED_VALUE:
            run_scripts(SCRIPTS_SHORT)
        else:
            print(f"Invalid {TREND_KEY} value: {trend_value}")
    else:
        print("Configuration not found or invalid")

if __name__ == "__main__":
    main()