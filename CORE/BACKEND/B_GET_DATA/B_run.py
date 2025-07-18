import yaml
import subprocess
import time
from datetime import datetime

# Settings
B_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
E_CANDLES_FILE = 'CORE/DATA/E_large_old_candles_data.yaml'
SCRIPTS_LARGE = ['CORE/BACKEND/B_GET_DATA/A_large/A_run.py']
SCRIPTS_SMALL = ['CORE/BACKEND/B_GET_DATA/B_small/B_run.py']

# Functions
def load_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def get_candle_close_time(data):
    return data[0]['candle_0_close_time']

def run_scripts(scripts):
    for script in scripts:
        result = subprocess.run(['python', script], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

def main():
    start_time = time.time()
    
    # Load YAML files
    b_data = load_yaml_file(B_CANDLES_FILE)
    e_data = load_yaml_file(E_CANDLES_FILE)
    
    # Get close times
    b_close_time = get_candle_close_time(b_data)
    e_close_time = get_candle_close_time(e_data)
    
    # Compare and run appropriate scripts
    scripts_to_run = SCRIPTS_LARGE if b_close_time != e_close_time else SCRIPTS_SMALL
    run_scripts(scripts_to_run)
    
    # Print execution time
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()