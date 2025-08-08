import yaml
import subprocess
import os

# Configuration
CONFIG_FILE = "CORE/DATA/config.yaml"
HIGH_LINE_KEY = "HIGH_LINE"
HIGH_LINE_UP_VALUE = "UP"
HIGH_LINE_DOWN_VALUE = "DOWN"
HIGH_COUNTER_KEY = "HIGH_COUNTER"
COUNTER_INCREMENT = 1
SCRIPTS = [
    "CORE/BACKEND/D_CHECK_HIGH_LOW_LINE/DBA_message_high_down.py",
    "CORE/BACKEND/Z_TOOLS/order_buy_short.py",
    # "CORE/BACKEND/Z_TOOLS/order_sell_long.py",
    # "CORE/BACKEND/Z_TOOLS/add_NOW_AMOUNT.py",
]

# Logic
def read_config(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Error: Configuration file {file_path} not found.")
        exit(1)

def write_config(file_path, lines, config):
    with open(file_path, 'w') as file:
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith(f"{HIGH_LINE_KEY}:"):
                file.write(f"{HIGH_LINE_KEY}: {config.get(HIGH_LINE_KEY, '')}\n")
            elif stripped_line.startswith(f"{HIGH_COUNTER_KEY}:"):
                file.write(f"{HIGH_COUNTER_KEY}: {config.get(HIGH_COUNTER_KEY, '')}\n")
            else:
                file.write(line)

def run_scripts(scripts):
    for script in scripts:
        try:
            subprocess.run(["python", script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to run script {script}: {e}")
            exit(1)
        except FileNotFoundError:
            print(f"Error: Script {script} not found.")
            exit(1)

def main():
    # Read original file lines to preserve order and comments
    try:
        with open(CONFIG_FILE, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: Configuration file {CONFIG_FILE} not found.")
        exit(1)

    # Load config as dictionary
    config = read_config(CONFIG_FILE)

    # Check if required keys exist
    if HIGH_LINE_KEY not in config:
        print(f"Error: {HIGH_LINE_KEY} not found in {CONFIG_FILE}.")
        exit(1)
    if HIGH_COUNTER_KEY not in config:
        print(f"Error: {HIGH_COUNTER_KEY} not found in {CONFIG_FILE}.")
        exit(1)

    # Update config if HIGH_LINE is UP
    if config[HIGH_LINE_KEY] == HIGH_LINE_UP_VALUE:
        config[HIGH_LINE_KEY] = HIGH_LINE_DOWN_VALUE
        config[HIGH_COUNTER_KEY] += COUNTER_INCREMENT

        # Write updated config back to file
        write_config(CONFIG_FILE, lines, config)

        # Run scripts
        run_scripts(SCRIPTS)

if __name__ == "__main__":
    main()