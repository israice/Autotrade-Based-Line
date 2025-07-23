import yaml
import os
import time
import subprocess

# Settings
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
GREEN_SCRIPT = "CORE/BACKEND/D_CHECK_SELL_PERCENT/A_long/A_run.py"
RED_SCRIPT = "CORE/BACKEND/D_CHECK_SELL_PERCENT/A_short/B_run.py"
TREND_GREEN = "GREEN"
TREND_RED = "RED"

# Functions
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def run_script(script_path):
    try:
        subprocess.run(['python', script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_path}: {e}")

def main():
    start_time = time.time()
    
    # Load configuration
    config = load_config(CONFIG_FILE)
    trend_large = config.get('TREND_LARGE')
    
    # Execute scripts based on TREND_LARGE value
    if trend_large == TREND_GREEN:
        run_script(GREEN_SCRIPT)
    elif trend_large == TREND_RED:
        run_script(RED_SCRIPT)
    else:
        print(f"Unknown TREND_LARGE value: {trend_large}")
    
    # Calculate and display execution time
    execution_time = time.time() - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()