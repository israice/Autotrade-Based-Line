import yaml
import subprocess
import time
from pathlib import Path

# Configuration
B_CANDLES_FILE = 'CORE/DATA/B_large_new_candles_data.yaml'
E_CANDLES_FILE = 'CORE/DATA/E_large_old_candles_data.yaml'
SCRIPTS_LARGE = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/A_run_large.py',
]
SCRIPTS_SMALL = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_run_small.py',
]

def read_candle_close_time(file_path):
    """Read candle_0_close_time from a YAML file."""
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0]['candle_0_close_time']
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def run_scripts(scripts):
    """Run a list of scripts and print their output."""
    for script in scripts:
        try:
            result = subprocess.run(['python', script], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            if output:
                print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")
            print(e.stderr.strip())

def main():
    """Compare candle close times and run appropriate scripts."""
    start_time = time.time()
    
    b_close_time = read_candle_close_time(B_CANDLES_FILE)
    e_close_time = read_candle_close_time(E_CANDLES_FILE)
    
    if b_close_time is None or e_close_time is None:
        # print("Failed to read one or both candle close times.")
        return
    
    if b_close_time != e_close_time:
        run_scripts(SCRIPTS_LARGE)
    else:
        run_scripts(SCRIPTS_SMALL)
    
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()