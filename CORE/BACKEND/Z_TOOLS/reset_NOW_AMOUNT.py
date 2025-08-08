import yaml
import os

# Configuration paths and values
SETTINGS_FILE = "CORE/DATA/user_settings.yaml"
CONFIG_FILE = "CORE/DATA/system_config.yaml"
START_AMOUNT_KEY = "START_AMOUNT"
NOW_AMOUNT_KEY = "NOW_AMOUNT"

# Function to read YAML file
def read_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {file_path}: {e}")
        return None

# Function to update specific value in YAML content while preserving lines
def update_yaml_line(file_path, key, new_value):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}:"):
                lines[i] = f"{key}: {new_value}\n"
                found = True
                break
        
        if not found:
            print(f"Error: Key {key} not found in {file_path}")
            return False
        
        with open(file_path, 'w') as file:
            file.writelines(lines)
        return True
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return False
    except Exception as e:
        print(f"Error: Failed to update {file_path}: {e}")
        return False

# Main logic
settings_data = read_yaml(SETTINGS_FILE)
if settings_data is None:
    exit(1)

if START_AMOUNT_KEY not in settings_data:
    print(f"Error: Key {START_AMOUNT_KEY} not found in {SETTINGS_FILE}")
    exit(1)

start_amount = settings_data[START_AMOUNT_KEY]
if not update_yaml_line(CONFIG_FILE, NOW_AMOUNT_KEY, start_amount):
    exit(1)