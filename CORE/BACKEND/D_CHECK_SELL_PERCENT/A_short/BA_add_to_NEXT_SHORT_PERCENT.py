import yaml
import time
from pathlib import Path

# Configuration settings
CONFIG_FILE = Path("CORE/DATA/C_temp_config.yaml")
SETTINGS_FILE = Path("settings.yaml")
PERCENTAGE_CHANGE_LARGE_KEY = "PERCENTAGE_CHANGE_LARGE"
NEXT_SHORT_PERCENT_KEY = "NEXT_SHORT_PERCENT"
SELL_ON_PERCENT_CHANGE_KEY = "SELL_ON_PERCENT_CHANGE"

def read_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        raise
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse {file_path}: {e}")
        raise

def write_yaml(file_path, data, original_lines):
    with open(file_path, 'w') as file:
        for line in original_lines:
            if line.strip().startswith(f"{NEXT_SHORT_PERCENT_KEY}:"):
                file.write(f"{NEXT_SHORT_PERCENT_KEY}: {data[NEXT_SHORT_PERCENT_KEY]:.3f}\n")
            else:
                file.write(line)

def main():
    start_time = time.time()
    
    # Read config files
    config_data = read_yaml(CONFIG_FILE)
    settings_data = read_yaml(SETTINGS_FILE)
    
    # Validate required keys
    if PERCENTAGE_CHANGE_LARGE_KEY not in config_data:
        print(f"Error: {PERCENTAGE_CHANGE_LARGE_KEY} not found in {CONFIG_FILE}")
        return
    if NEXT_SHORT_PERCENT_KEY not in config_data:
        print(f"Error: {NEXT_SHORT_PERCENT_KEY} not found in {CONFIG_FILE}")
        return
    if SELL_ON_PERCENT_CHANGE_KEY not in settings_data:
        print(f"Error: {SELL_ON_PERCENT_CHANGE_KEY} not found in {SETTINGS_FILE}")
        return
    
    percentage_change_large = config_data[PERCENTAGE_CHANGE_LARGE_KEY]
    next_short_percent = config_data[NEXT_SHORT_PERCENT_KEY]
    sell_on_percent_change = settings_data[SELL_ON_PERCENT_CHANGE_KEY]
    
    # Check if adjustment is needed
    if percentage_change_large < next_short_percent:
        
        # Calculate how many times to apply sell_on_percent_change
        while next_short_percent >= percentage_change_large:
            next_short_percent -= sell_on_percent_change
        
        # Round to 3 decimal places
        config_data[NEXT_SHORT_PERCENT_KEY] = round(next_short_percent, 3)
        
        # Read original file lines to preserve comments and order
        with open(CONFIG_FILE, 'r') as file:
            original_lines = file.readlines()
        
        # Write updated value back to file
        write_yaml(CONFIG_FILE, config_data, original_lines)
    
    # Print execution time
    # print(f"Script execution time: {time.time() - start_time:.3f} seconds")

if __name__ == "__main__":
    main()