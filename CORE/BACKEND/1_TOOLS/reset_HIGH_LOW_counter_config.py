import yaml
import os
from datetime import datetime

# Configuration settings
CONFIG_FILE_PATH = "CORE/DATA/C_temp_config.yaml"
HIGH_COUNTER_KEY = "HIGH_COUNTER"
LOW_COUNTER_KEY = "LOW_COUNTER"
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
    high_counter_found = False
    low_counter_found = False
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(f"{HIGH_COUNTER_KEY}:"):
            updated_lines.append(f"{HIGH_COUNTER_KEY}: {NEW_VALUE}\n")
            high_counter_found = True
        elif stripped_line.startswith(f"{LOW_COUNTER_KEY}:"):
            updated_lines.append(f"{LOW_COUNTER_KEY}: {NEW_VALUE}\n")
            low_counter_found = True
        else:
            updated_lines.append(line)
    
    if not high_counter_found:
        print(f"Error: '{HIGH_COUNTER_KEY}' not found in configuration file.")
        exit(1)
    if not low_counter_found:
        print(f"Error: '{LOW_COUNTER_KEY}' not found in configuration file.")
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
