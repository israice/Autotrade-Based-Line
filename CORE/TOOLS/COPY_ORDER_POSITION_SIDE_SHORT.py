import yaml
import os

# ================== CONFIGURATION ==================
CONFIG_FILE = "CORE/DATA/DD_ORDER_BODY.yaml"
NOW_AMOUNT_KEY = "ORDER_POSITION_SIDE"
# You can put any value here: number, string, null
RESET_VALUE = 'SHORT'
# ====================================================

# Function to update specific value in YAML content while preserving lines
def update_yaml_line(file_path, key, new_value):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Convert Python value to YAML-compatible string
        if new_value is None:
            yaml_value = "null"
        else:
            yaml_value = str(new_value)  # No quotes for strings

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

# Main logic: reset NOW_AMOUNT to RESET_VALUE
if not update_yaml_line(CONFIG_FILE, NOW_AMOUNT_KEY, RESET_VALUE):
    exit(1)