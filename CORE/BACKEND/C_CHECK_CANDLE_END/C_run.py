import yaml
import subprocess
import time
from pathlib import Path

# Settings
LARGE_NEW_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
LARGE_OLD_CANDLES_FILE = 'CORE/DATA/E_large_old_candles_data.yaml'
SMALL_NEW_CANDLES_FILE = 'CORE/DATA/A_small_new_candles_data.yaml'
SMALL_OLD_CANDLES_FILE = 'CORE/DATA/D_small_old_candles_data.yaml'
CANDLE_OPEN_TIME_KEY = 'candle_0_open_time'
SCRIPTS_LARGE = ['CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_run_large.py']
SCRIPTS_SMALL = ['CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_run_small.py']

def read_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0][CANDLE_OPEN_TIME_KEY] if data and isinstance(data, list) and CANDLE_OPEN_TIME_KEY in data[0] else None
    except (FileNotFoundError, yaml.YAMLError, KeyError):
        return None

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        try:
            result = subprocess.run(['python', script], capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e.stderr.strip()}")
    end_time = time.time()
    print(f"Script execution time: {end_time - start_time:.2f} seconds")

def main():
    large_new_time = read_yaml_file(LARGE_NEW_CANDLES_FILE)
    large_old_time = read_yaml_file(LARGE_OLD_CANDLES_FILE)
    
    if large_new_time is not None and large_old_time is not None and large_new_time != large_old_time:
        run_scripts(SCRIPTS_LARGE)
    else:
        small_new_time = read_yaml_file(SMALL_NEW_CANDLES_FILE)
        small_old_time = read_yaml_file(SMALL_OLD_CANDLES_FILE)
        
        if small_new_time is not None and small_old_time is not None and small_new_time != small_old_time:
            run_scripts(SCRIPTS_SMALL)

if __name__ == '__main__':
    main()