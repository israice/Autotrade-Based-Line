import yaml
import time
from pathlib import Path
import subprocess

# Settings
LARGE_CANDLE_FILE = "CORE/DATA/A_candle.yaml"
CLONE_CANDLE_FILE = "CORE/BACKEND/Y_COPY_DATA/YA_clone_candles.yaml"
SCRIPTS_HIGH = [
    "CORE/BACKEND/C_CHECK_CANDLE_END/CAA_message_up.py",
    "CORE/BACKEND/Z_TOOLS/reset_config_lines.py", 
    "CORE/BACKEND/Z_TOOLS/reset_NOW_AMOUNT.py",  
    "CORE/BACKEND/Z_TOOLS/order_sell_long.py",
]
SCRIPTS_LOW = [
    "CORE/BACKEND/C_CHECK_CANDLE_END/CBA_message_down.py",
    "CORE/BACKEND/Z_TOOLS/reset_config_lines.py",   
    "CORE/BACKEND/Z_TOOLS/reset_NOW_AMOUNT.py",  
    "CORE/BACKEND/Z_TOOLS/order_sell_short.py",
]
CANDLE_KEY = "candle_0_open"

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data[0] if isinstance(data, list) else data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_candle_value(data, key):
    if data is None:
        return None
    return data.get(key)

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        try:
            result = subprocess.run(['python', script], capture_output=True, text=True)
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        except Exception as e:
            print(f"Error running {script}: {e}")
    end_time = time.time()
    # print(f"Scripts execution time: {end_time - start_time:.2f} seconds")

def main():
    large_candle_data = load_yaml_file(LARGE_CANDLE_FILE)
    clone_candle_data = load_yaml_file(CLONE_CANDLE_FILE)
    
    large_value = get_candle_value(large_candle_data, CANDLE_KEY)
    clone_value = get_candle_value(clone_candle_data, CANDLE_KEY)
    
    if large_value is None or clone_value is None or large_value == clone_value:
        return
    
    try:
        large_float = float(large_value)
        clone_float = float(clone_value)
        
        if large_float > clone_float:
            run_scripts(SCRIPTS_HIGH)
        elif large_float < clone_float:
            run_scripts(SCRIPTS_LOW)
    except ValueError as e:
        print(f"Error converting values to float: {e}")

if __name__ == "__main__":
    main()