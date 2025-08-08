import yaml
import os

# Configuration
CONFIG_FILE_PATH = "CORE/DATA/triggers_config.yaml"
HIGH_LINE_KEY = "HIGH_LINE"
LOW_LINE_KEY = "LOW_LINE"
HIGH_COUNTER_KEY = "HIGH_COUNTER"
LOW_COUNTER_KEY = "LOW_COUNTER"
NEW_LINE_VALUE = "LINE"
NEW_COUNTER_VALUE = 0

# Logic
def update_config():
    try:
        # Read the config file
        with open(CONFIG_FILE_PATH, 'r') as file:
            lines = file.readlines()

        # Process each line
        updated_lines = []
        keys_to_replace = {
            HIGH_LINE_KEY: NEW_LINE_VALUE,
            LOW_LINE_KEY: NEW_LINE_VALUE,
            HIGH_COUNTER_KEY: NEW_COUNTER_VALUE,
            LOW_COUNTER_KEY: NEW_COUNTER_VALUE
        }
        found_keys = set()

        for line in lines:
            stripped_line = line.strip()
            # Skip empty lines and comments
            if not stripped_line or stripped_line.startswith('#'):
                updated_lines.append(line)
                continue

            # Check each key to replace
            for key, new_value in keys_to_replace.items():
                if stripped_line.startswith(f"{key}:"):
                    updated_lines.append(f"{key}: {new_value}\n")
                    found_keys.add(key)
                    break
            else:
                updated_lines.append(line)

        # Check if all required keys were found
        missing_keys = set(keys_to_replace.keys()) - found_keys
        if missing_keys:
            for key in missing_keys:
                print(f"Error: Key '{key}' not found in {CONFIG_FILE_PATH}")
            return

        # Write updated content back to file
        with open(CONFIG_FILE_PATH, 'w') as file:
            file.writelines(updated_lines)

    except FileNotFoundError:
        print(f"Error: File '{CONFIG_FILE_PATH}' not found")
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    update_config()