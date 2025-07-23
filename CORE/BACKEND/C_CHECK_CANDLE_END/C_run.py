import yaml
import subprocess
import time
from pathlib import Path

# Configuration
LARGE_NEW_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
LARGE_OLD_CANDLES_FILE = 'CORE/DATA/E_large_old_candles_data.yaml'
SMALL_NEW_CANDLES_FILE = 'CORE/DATA/A_small_new_candles_data.yaml'
SMALL_OLD_CANDLES_FILE = 'CORE/DATA/D_small_old_candles_data.yaml'
CANDLE_KEY = 'candle_0_open_time'
SCRIPTS_LARGE = ['CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_run_large.py']
SCRIPTS_SMALL = ['CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_run_small.py']

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0][CANDLE_KEY] if data and isinstance(data, list) and CANDLE_KEY in data[0] else None
    except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            try:
                result = subprocess.run(['python', str(script_path)], capture_output=True, text=True, check=True)
                if result.stdout:
                    print(result.stdout, end='')
                if result.stderr:
                    print(result.stderr, end='')
            except subprocess.CalledProcessError as e:
                print(f"Error running {script}: {e}")
        else:
            print(f"Script not found: {script}")
    end_time = time.time()
    # print(f"Execution time: {end_time - start_time:.2f} seconds")

def main():
    large_new_time = load_yaml_file(LARGE_NEW_CANDLES_FILE)
    large_old_time = load_yaml_file(LARGE_OLD_CANDLES_FILE)

    if large_new_time and large_old_time and large_new_time != large_old_time:
        run_scripts(SCRIPTS_LARGE)
    else:
        small_new_time = load_yaml_file(SMALL_NEW_CANDLES_FILE)
        small_old_time = load_yaml_file(SMALL_OLD_CANDLES_FILE)
        if small_new_time and small_old_time and small_new_time != small_old_time:
            run_scripts(SCRIPTS_SMALL)

if __name__ == '__main__':
    main()