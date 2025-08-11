import yaml
import subprocess

# Configuration settings and variables
CONFIG_FILE = 'CORE/DATA/triggers_config.yaml'
GREEN_LIST = [
    "CORE/BACKEND/Z_TOOLS/message_up.py",
    "CORE/BACKEND/Z_TOOLS/add_1_to_COUNTER_OPEN_CROSSING.py",
]
RED_LIST = [
    "CORE/BACKEND/Z_TOOLS/message_down.py",
    "CORE/BACKEND/Z_TOOLS/add_1_to_COUNTER_OPEN_CROSSING.py",
]
GREEN_STATUS = 'GREEN'
RED_STATUS = 'RED'
PERCENT_STATUS_KEY = 'PERCENT_STATUS'
TREND_STATUS_KEY = 'TREND_STATUS'

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) or {}

def save_config(file_path, new_trend_status):
    # Read the original file to preserve comments and structure
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Update only the TREND_STATUS line
    trend_status_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{TREND_STATUS_KEY}:'):
            lines[i] = f"{TREND_STATUS_KEY}: {new_trend_status}\n"
            trend_status_found = True
            break
    
    # If TREND_STATUS is not found, append it
    if not trend_status_found:
        lines.append(f"{TREND_STATUS_KEY}: {new_trend_status}\n")
    
    # Write back to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)

def run_scripts(script_list):
    for script in script_list:
        subprocess.run(['python', script])

def main():
    config = load_config(CONFIG_FILE)
    percent_status = config.get(PERCENT_STATUS_KEY, 0)
    trend_status = config.get(TREND_STATUS_KEY, '')

    if percent_status > 0 and trend_status != GREEN_STATUS:
        save_config(CONFIG_FILE, GREEN_STATUS)
        if trend_status != GREEN_STATUS:
            run_scripts(GREEN_LIST)
    elif percent_status < 0 and trend_status != RED_STATUS:
        save_config(CONFIG_FILE, RED_STATUS)
        if trend_status != RED_STATUS:
            run_scripts(RED_LIST)

if __name__ == "__main__":
    main()