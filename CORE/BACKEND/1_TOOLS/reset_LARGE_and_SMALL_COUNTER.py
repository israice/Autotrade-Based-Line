import yaml
import os
from datetime import datetime

# Configuration settings
CONFIG_FILE_PATH = "CORE/DATA/C_temp_config.yaml"
SMALL_COUNTER_KEY = "SMALL_OPEN_COUNTER"
LARGE_COUNTER_KEY = "LARGE_OPEN_COUNTER"
NEW_VALUE = 0

def read_config(file_path):
    """Read the YAML configuration file."""
    if not os.path.exists(file_path):
        print(f"Error: Configuration file '{file_path}' not found.")
        exit(1)
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def update_config_file(file_path, config_data):
    """Update the YAML configuration file while preserving comments and empty lines."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    updated_lines = []
    SMALL_counter_found = False
    LARGE_counter_found = False
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(f"{SMALL_COUNTER_KEY}:"):
            updated_lines.append(f"{SMALL_COUNTER_KEY}: {NEW_VALUE}\n")
            SMALL_counter_found = True
        elif stripped_line.startswith(f"{LARGE_COUNTER_KEY}:"):
            updated_lines.append(f"{LARGE_COUNTER_KEY}: {NEW_VALUE}\n")
            LARGE_counter_found = True
        else:
            updated_lines.append(line)
    
    if not SMALL_counter_found:
        print(f"Error: '{SMALL_COUNTER_KEY}' not found in configuration file.")
        exit(1)
    if not LARGE_counter_found:
        print(f"Error: '{LARGE_COUNTER_KEY}' not found in configuration file.")
        exit(1)
    
    with open(file_path, 'w') as file:
        file.writelines(updated_lines)

def main():
    """Main function to execute the script."""
    start_time = datetime.now()
    
    config_data = read_config(CONFIG_FILE_PATH)
    update_config_file(CONFIG_FILE_PATH, config_data)
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    # print(f"Execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()
