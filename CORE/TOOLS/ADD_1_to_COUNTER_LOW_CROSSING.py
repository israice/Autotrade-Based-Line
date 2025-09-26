import yaml
import os

# ================== CONFIGURATION ==================
CONFIG_FILE = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"
NOW_AMOUNT_KEY = "COUNTER_LOW_CROSSING"
INCREMENT_VALUE = 1  # Value to increment by
# ====================================================

# Function to read current value from YAML
def read_yaml_value(file_path, key):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data.get(key)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except Exception as e:
        print(f"Error: Failed to read {file_path}: {e}")
        return None

# Function to update specific value in YAML content while preserving lines
def update_yaml_line(file_path, key, new_value):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Convert Python value to YAML-compatible string
        if isinstance(new_value, str):
            yaml_value = f"'{new_value}'"  # wrap in quotes if it's string
        elif new_value is None:
            yaml_value = "null"
        else:
            yaml_value = str(new_value)

        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}:"):
                lines[i] = f"{key}: {yaml_value}\n"
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

# Main logic: increment NOW_AMOUNT_KEY by INCREMENT_VALUE
current_value = read_yaml_value(CONFIG_FILE, NOW_AMOUNT_KEY)
if current_value is None:
    exit(1)

# Check if current_value is a number
if not isinstance(current_value, (int, float)):
    print(f"Error: Current value of {NOW_AMOUNT_KEY} is not a number")
    exit(1)

# Increment the value
new_value = current_value + INCREMENT_VALUE

# Update the YAML file with new value
if not update_yaml_line(CONFIG_FILE, NOW_AMOUNT_KEY, new_value):
    exit(1)