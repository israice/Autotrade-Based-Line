import yaml
import os
import time
from pathlib import Path

# Configuration
TEMP_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"
SETTINGS_PATH = "settings.yaml"
PERCENTAGE_CHANGE_LARGE_KEY = "PERCENTAGE_CHANGE_LARGE"
NEXT_LONG_PERCENT_KEY = "NEXT_LONG_PERCENT"
SELL_ON_PERCENT_CHANGE_KEY = "SELL_ON_PERCENT_CHANGE"

def read_yaml_preserve_format(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data = yaml.safe_load(''.join(lines))
    return data, lines

def write_yaml_preserve_format(file_path, lines, key, new_value):
    with open(file_path, 'w') as file:
        for line in lines:
            if line.strip().startswith(f"{key}:"):
                file.write(f"{key}: {new_value:.3f}\n")
            else:
                file.write(line)

def main():
    start_time = time.time()
    
    # Check if files exist
    if not os.path.exists(TEMP_CONFIG_PATH):
        print(f"Error: File {TEMP_CONFIG_PATH} not found")
        return
    if not os.path.exists(SETTINGS_PATH):
        print(f"Error: File {SETTINGS_PATH} not found")
        return

    # Read YAML files
    try:
        temp_config, temp_lines = read_yaml_preserve_format(TEMP_CONFIG_PATH)
        settings_config, _ = read_yaml_preserve_format(SETTINGS_PATH)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML files - {e}")
        return

    # Check if required keys exist
    if PERCENTAGE_CHANGE_LARGE_KEY not in temp_config:
        print(f"Error: {PERCENTAGE_CHANGE_LARGE_KEY} not found in {TEMP_CONFIG_PATH}")
        return
    if NEXT_LONG_PERCENT_KEY not in temp_config:
        print(f"Error: {NEXT_LONG_PERCENT_KEY} not found in {TEMP_CONFIG_PATH}")
        return
    if SELL_ON_PERCENT_CHANGE_KEY not in settings_config:
        print(f"Error: {SELL_ON_PERCENT_CHANGE_KEY} not found in {SETTINGS_PATH}")
        return

    # Get values
    percentage_change_large = temp_config[PERCENTAGE_CHANGE_LARGE_KEY]
    next_long_percent = temp_config[NEXT_LONG_PERCENT_KEY]
    sell_on_percent_change = settings_config[SELL_ON_PERCENT_CHANGE_KEY]

    # Compare and update if needed
    if percentage_change_large > next_long_percent:
        new_next_long_percent = percentage_change_large + sell_on_percent_change
        write_yaml_preserve_format(TEMP_CONFIG_PATH, temp_lines, NEXT_LONG_PERCENT_KEY, new_next_long_percent)

    # Print execution time
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.3f} seconds")

if __name__ == "__main__":
    main()