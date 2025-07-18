import yaml
import subprocess
import time
from pathlib import Path

# Configuration
NEW_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
OLD_CANDLES_FILE = 'CORE/DATA/E_large_old_candles_data.yaml'
SCRIPTS_LONG = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_long/A_run.py'
]
SCRIPTS_SHORT = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/B_short/B_run.py'
]
CANDLE_KEY = 'candle_0_open'

# Functions
def read_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0][CANDLE_KEY]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def run_scripts(scripts):
    for script in scripts:
        try:
            result = subprocess.run(['python', script], capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")

def main():
    start_time = time.time()
    
    new_value = read_yaml_file(NEW_CANDLES_FILE)
    old_value = read_yaml_file(OLD_CANDLES_FILE)
    
    if new_value is None or old_value is None:
        # print("Failed to read one or both candle values")
        return
    
    new_value = float(new_value)
    old_value = float(old_value)
    
    if new_value > old_value:
        run_scripts(SCRIPTS_LONG)
    elif new_value < old_value:
        run_scripts(SCRIPTS_SHORT)
    # else:
    #     print("Candle values are equal, no scripts executed")
    
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()