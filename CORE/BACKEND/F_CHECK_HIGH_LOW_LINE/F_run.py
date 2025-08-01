import yaml
import subprocess
import time
from pathlib import Path

# Configuration variables
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
HIGH_SCRIPT = "CORE/BACKEND/F_CHECK_HIGH_LOW_LINE/A_high/A_run.py"
LOW_SCRIPT = "CORE/BACKEND/F_CHECK_HIGH_LOW_LINE/B_low/B_run.py"
STATUS_KEY = "LARGE_OPEN_STATUS"
GREEN_STATUS = "GREEN"
RED_STATUS = "RED"

def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config[STATUS_KEY]

def run_script(script_path):
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())

def main():
    start_time = time.time()
    project_root = Path.cwd()
    config_path = project_root / CONFIG_FILE
    status = read_config(config_path)
    
    if status == GREEN_STATUS:
        run_script(project_root / HIGH_SCRIPT)
    elif status == RED_STATUS:
        run_script(project_root / LOW_SCRIPT)
    
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()