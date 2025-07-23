import yaml
import time
from pathlib import Path

# Configuration settings
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"
SETTINGS_FILE = "settings.yaml"
PERCENTAGE_CHANGE_KEY = "PERCENTAGE_CHANGE_LARGE"
NEXT_SHORT_PERCENT_KEY = "NEXT_SHORT_PERCENT"
SELL_ON_PERCENT_KEY = "SELL_ON_PERCENT_CHANGE"

def read_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse {file_path}: {e}")
        exit(1)

def write_yaml(file_path, data, original_lines):
    with open(file_path, 'w') as file:
        for line in original_lines:
            if line.strip().startswith(f"{NEXT_SHORT_PERCENT_KEY}:"):
                new_value = data[NEXT_SHORT_PERCENT_KEY]
                file.write(f"{NEXT_SHORT_PERCENT_KEY}: {new_value:.3f}\n")
            else:
                file.write(line)

def main():
    start_time = time.time()
    
    # Read config files
    config_data = read_yaml(CONFIG_FILE)
    settings_data = read_yaml(SETTINGS_FILE)
    
    # Extract values
    try:
        percentage_change = config_data[PERCENTAGE_CHANGE_KEY]
        next_short_percent = config_data[NEXT_SHORT_PERCENT_KEY]
        sell_on_percent = settings_data[SELL_ON_PERCENT_KEY]
    except KeyError as e:
        print(f"Error: Key {e} not found in configuration files")
        exit(1)
    
    # Check condition and update if necessary
    if percentage_change < next_short_percent:
        new_value = next_short_percent - sell_on_percent
        
        # Read original file lines to preserve comments and order
        with open(CONFIG_FILE, 'r') as file:
            original_lines = file.readlines()
        
        # Update config data
        config_data[NEXT_SHORT_PERCENT_KEY] = round(new_value, 3)
        
        # Write back to file
        write_yaml(CONFIG_FILE, config_data, original_lines)
    
    # Print execution time
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.3f} seconds")

main()