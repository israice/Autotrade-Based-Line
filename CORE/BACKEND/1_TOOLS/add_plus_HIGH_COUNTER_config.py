import yaml
import os
import time
from pathlib import Path

# Configuration settings
CONFIG_FILE_PATH = Path("CORE/DATA/C_temp_config.yaml")
VARIABLE_TO_INCREMENT = "HIGH_COUNTER"
CONFIG_INCREMENT = 1

def load_config(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found at {file_path}")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def update_config(file_path, config_data, variable, increment):
    if variable not in config_data:
        raise KeyError(f"Variable {variable} not found in config file")
    
    config_data[variable] += increment
    
    # Read original file content to preserve comments and structure
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Update only the specific line with the variable
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{variable}:"):
            lines[i] = f"{variable}: {config_data[variable]}\n"
            break
    
    # Write back to file
    with open(file_path, 'w') as file:
        file.writelines(lines)

def main():
    start_time = time.time()
    
    config_data = load_config(CONFIG_FILE_PATH)
       
    update_config(CONFIG_FILE_PATH, config_data, VARIABLE_TO_INCREMENT, CONFIG_INCREMENT)
        
    execution_time = time.time() - start_time
    # print(f"Script execution time: {execution_time:.4f} seconds")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")