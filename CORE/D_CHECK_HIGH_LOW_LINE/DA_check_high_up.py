import yaml
import os
from pathlib import Path
import subprocess

# Configuration
CONFIG_FILE = "config.yaml"
HIGH_LINE_KEY = "HIGH_LINE"
HIGH_COUNTER_KEY = "HIGH_COUNTER"
LINE_STATUS = "UP"
COUNTER_INCREMENT = 1
SCRIPTS = [
    "CORE/D_CHECK_HIGH_LOW_LINE/DAA_message_high_up.py",
    "CORE/Z_TOOLS/order_buy_long.py",
    "CORE/Z_TOOLS/order_sell_short.py",
    "CORE/Z_TOOLS/add_NOW_AMOUNT.py",
]

# Logic
def read_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Error: Configuration file {file_path} not found")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse {file_path}: {e}")
        exit(1)

def write_config(file_path, config_lines, high_line_value, high_counter_value):
    updated_lines = []
    high_line_found = False
    high_counter_found = False

    for line in config_lines:
        stripped_line = line.strip()
        if stripped_line.startswith(f"{HIGH_LINE_KEY}:"):
            high_line_found = True
            line = f"{HIGH_LINE_KEY}: {high_line_value}\n"
        elif stripped_line.startswith(f"{HIGH_COUNTER_KEY}:"):
            high_counter_found = True
            line = f"{HIGH_COUNTER_KEY}: {high_counter_value}\n"
        updated_lines.append(line)

    if not high_line_found:
        print(f"Error: {HIGH_LINE_KEY} not found in {CONFIG_FILE}")
        exit(1)
    if not high_counter_found:
        print(f"Error: {HIGH_COUNTER_KEY} not found in {CONFIG_FILE}")
        exit(1)

    with open(file_path, 'w') as file:
        file.writelines(updated_lines)

def run_scripts(scripts):
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            print(f"Error: Script {script} not found")
            continue
        try:
            subprocess.run(["python", str(script_path)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to run {script}: {e}")
        except Exception as e:
            print(f"Error: Unexpected error running {script}: {e}")

def main():
    config_path = Path(CONFIG_FILE)
    
    # Read original config file content to preserve comments and order
    try:
        with open(config_path, 'r') as file:
            config_lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: Configuration file {CONFIG_FILE} not found")
        exit(1)

    # Parse config
    config = read_config(config_path)
    
    # Check HIGH_LINE value and update if necessary
    if HIGH_LINE_KEY not in config:
        print(f"Error: {HIGH_LINE_KEY} not found in {CONFIG_FILE}")
        exit(1)
    if HIGH_COUNTER_KEY not in config:
        print(f"Error: {HIGH_COUNTER_KEY} not found in {CONFIG_FILE}")
        exit(1)

    if config[HIGH_LINE_KEY] != LINE_STATUS:
        # Update config
        new_counter = int(config[HIGH_COUNTER_KEY]) + COUNTER_INCREMENT
        write_config(config_path, config_lines, LINE_STATUS, new_counter)
        
        # Run scripts
        run_scripts(SCRIPTS)

if __name__ == "__main__":
    main()