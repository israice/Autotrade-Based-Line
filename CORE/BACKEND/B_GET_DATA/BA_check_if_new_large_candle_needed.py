import yaml
import datetime
import os
from pathlib import Path
import subprocess
import time

# File paths (relative to project root where .env is located)
A_CANDLES_FILE = 'CORE/DATA/A_small_new_candles_data.yaml'
B_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'

# Variable names for candle_0_close_time
A_CANDLE_CLOSE_TIME_KEY = 'candle_0_close_time'
B_CANDLE_CLOSE_TIME_KEY = 'candle_0_close_time'

# List of scripts to run
SCRIPTS = [
    'CORE/BACKEND/B_GET_DATA/BAA_get_large_candles.py',
]

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0] if data and isinstance(data, list) else {}
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return {}

def parse_datetime(datetime_str):
    try:
        return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error parsing datetime {datetime_str}: {str(e)}")
        return None

def run_scripts():
    start_time = time.time()
    for script in SCRIPTS:
        script_path = Path(script)
        if not script_path.exists():
            print(f"Script not found: {script}")
            continue
        try:
            result = subprocess.run(['python', str(script_path)], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            if output:
                print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e.stderr.strip()}")
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

def main():
    # Load YAML files
    a_data = load_yaml_file(A_CANDLES_FILE)
    b_data = load_yaml_file(B_CANDLES_FILE)
    
    # Get close times
    a_close_time_str = a_data.get(A_CANDLE_CLOSE_TIME_KEY)
    b_close_time_str = b_data.get(B_CANDLE_CLOSE_TIME_KEY)
    
    if not a_close_time_str or not b_close_time_str:
        print("Missing close time in one or both files")
        return
    
    # Parse datetimes
    a_close_time = parse_datetime(a_close_time_str)
    b_close_time = parse_datetime(b_close_time_str)
    
    if a_close_time is None or b_close_time is None:
        print("Failed to parse one or both close times")
        return
    
    # Compare and run scripts if condition met
    if a_close_time > b_close_time:
        run_scripts()

if __name__ == "__main__":
    main()