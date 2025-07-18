import yaml
import subprocess
import time
from pathlib import Path

# Configuration
NEW_CANDLES_FILE = 'CORE/DATA/A_small_new_candles_data.yaml'
OLD_CANDLES_FILE = 'CORE/DATA/D_small_old_candles_data.yaml'
SCRIPTS_LONG = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/A_long/A_run.py',
]
SCRIPTS_SHORT = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/B_small/B_short/B_run.py',
]
CANDLE_KEY = 'candle_0_open'

def load_yaml_file(file_path):
    """Load and return data from a YAML file."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_candle_value(data, key):
    """Extract candle value from YAML data."""
    if data and isinstance(data, list) and len(data) > 0:
        return float(data[0].get(key, 0))
    return None

def run_scripts(scripts):
    """Execute a list of scripts and print their output."""
    start_time = time.time()
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            try:
                result = subprocess.run(['python', str(script_path)], 
                                     capture_output=True, 
                                     text=True, 
                                     check=True)
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(result.stderr.strip())
            except subprocess.CalledProcessError as e:
                print(f"Error running {script}: {e}")
        else:
            print(f"Script not found: {script}")
    end_time = time.time()
    # print(f"Total execution time: {end_time - start_time:.2f} seconds")

def main():
    """Compare candle values and run appropriate scripts."""
    new_data = load_yaml_file(NEW_CANDLES_FILE)
    old_data = load_yaml_file(OLD_CANDLES_FILE)
    
    new_value = get_candle_value(new_data, CANDLE_KEY)
    old_value = get_candle_value(old_data, CANDLE_KEY)
    
    if new_value is None or old_value is None:
        print("Error: Could not retrieve candle values")
        return
    
    if new_value > old_value:
        run_scripts(SCRIPTS_LONG)
    elif new_value < old_value:
        run_scripts(SCRIPTS_SHORT)
    # else:
    #     print("Candle values are equal. No scripts will be executed.")

if __name__ == "__main__":
    main()