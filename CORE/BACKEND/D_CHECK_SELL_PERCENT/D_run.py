import yaml
import os
import subprocess
import time
from pathlib import Path

# Configuration variables
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
NEXT_LONG_PERCENT = "NEXT_LONG_PERCENT"
NEXT_SHORT_PERCENT = "NEXT_SHORT_PERCENT"
PERCENTAGE_CHANGE_LARGE = "PERCENTAGE_CHANGE_LARGE"
LONG_SCRIPTS = ["CORE/BACKEND/D_CHECK_SELL_PERCENT/A_long/A_run.py"]
SHORT_SCRIPTS = ["CORE/BACKEND/D_CHECK_SELL_PERCENT/A_short/B_run.py"]

def load_config():
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    required_keys = [PERCENTAGE_CHANGE_LARGE, NEXT_LONG_PERCENT, NEXT_SHORT_PERCENT]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise KeyError(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    return config

def run_scripts(scripts):
    start_time = time.time()
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script}")
        
        process = subprocess.run(['python', str(script_path)], capture_output=True, text=True)
        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(f"Error in {script}: {process.stderr.strip()}")
    
    execution_time = time.time() - start_time
    # print(f"Total execution time for scripts: {execution_time:.2f} seconds")

def main():
    try:
        config = load_config()
        percentage_change = config[PERCENTAGE_CHANGE_LARGE]
        next_long_percent = config[NEXT_LONG_PERCENT]
        next_short_percent = config[NEXT_SHORT_PERCENT]

        if percentage_change >= 0:
            if next_long_percent < percentage_change:
                run_scripts(LONG_SCRIPTS)
        else:
            if percentage_change < next_short_percent:
                run_scripts(SHORT_SCRIPTS)
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except KeyError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()