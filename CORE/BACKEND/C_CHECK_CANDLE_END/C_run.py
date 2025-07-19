import yaml
import subprocess
import time
from pathlib import Path

# Configuration
PROJECT_ROOT = Path.cwd()
B_LARGE_YAML = 'CORE/DATA/B_large_new_candles_data.yaml'
E_LARGE_YAML = 'CORE/DATA/E_large_old_candles_data.yaml'
A_SMALL_YAML = 'CORE/DATA/A_small_new_candles_data.yaml'
D_SMALL_YAML = 'CORE/DATA/D_small_old_candles_data.yaml'

SCRIPTS_LARGE = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_run_large.py',
]
SCRIPTS_SMALL = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_run_small.py',
]

def load_yaml_file(file_path):
    try:
        with open(PROJECT_ROOT / file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0].get('candle_0_open_time') if data else None
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        script_path = PROJECT_ROOT / script
        try:
            result = subprocess.run(['python', str(script_path)], capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")
    end_time = time.time()
    # print(f"Script execution time: {end_time - start_time:.2f} seconds")

def main():
    # Compare large candle times
    b_large_time = load_yaml_file(B_LARGE_YAML)
    e_large_time = load_yaml_file(E_LARGE_YAML)

    if b_large_time is None or e_large_time is None or b_large_time == e_large_time:
        # Compare small candle times
        a_small_time = load_yaml_file(A_SMALL_YAML)
        d_small_time = load_yaml_file(D_SMALL_YAML)
        
        if a_small_time is not None and d_small_time is not None and a_small_time != d_small_time:
            print("Small candle times differ, running small scripts...")
            run_scripts(SCRIPTS_SMALL)
    else:
        print("Large candle times differ, running large scripts...")
        run_scripts(SCRIPTS_LARGE)

if __name__ == '__main__':
    main()