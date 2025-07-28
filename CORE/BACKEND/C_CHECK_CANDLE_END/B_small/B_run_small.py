import yaml
import subprocess
import time
from pathlib import Path

# Configuration
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
TREND_KEY = "SMALL_OPEN_STATUS"
GREEN_VALUE = "GREEN"
RED_VALUE = "RED"

SCRIPTS_LONG = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/A_long/A_run.py',
]
SCRIPTS_SHORT = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_short/B_run.py',
]

# Functions
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def run_script(script_path):
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    output = result.stdout.strip()
    if output:
        print(output)

def main():
    start_time = time.time()
    project_root = Path.cwd()
    config_path = project_root / CONFIG_FILE
    config = load_config(config_path)
    trend_value = config.get(TREND_KEY)

    scripts_to_run = []
    if trend_value == GREEN_VALUE:
        scripts_to_run = SCRIPTS_LONG
    elif trend_value == RED_VALUE:
        scripts_to_run = SCRIPTS_SHORT

    for script in scripts_to_run:
        script_path = project_root / script
        run_script(script_path)

    execution_time = time.time() - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()