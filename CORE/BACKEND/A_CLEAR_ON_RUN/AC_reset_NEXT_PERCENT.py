import time
import os
from pathlib import Path
import ruamel.yaml

# --- Settings ---
PROJECT_ROOT = Path.cwd()  # Root directory where .env file is located
SOURCE_CONFIG_PATH = "settings.yaml"  # Path to source YAML file relative to project root
TARGET_CONFIG_PATH = "CORE/DATA/C_temp_config.yaml"  # Path to target YAML file relative to project root
SOURCE_KEY = "SELL_ON_PERCENT_CHANGE"  # Key to read from source file
TARGET_KEYS = ["NEXT_LONG_PERCENT", "NEXT_SHORT_PERCENT"]  # Keys to update in target file
ENCODING = "utf-8"  # File encoding

# --- Functions ---
def load_yaml(file_path):
    """Load a YAML file while preserving comments and structure."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    try:
        with open(file_path, "r", encoding=ENCODING) as file:
            return yaml.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error loading YAML file {file_path}: {str(e)}")

def save_yaml(data, file_path):
    """Save data to a YAML file while preserving structure."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    try:
        with open(file_path, "w", encoding=ENCODING) as file:
            yaml.dump(data, file)
    except Exception as e:
        raise Exception(f"Error saving YAML file {file_path}: {str(e)}")

def get_source_value(source_path, key):
    """Read the value of the specified key from the source YAML file."""
    source_data = load_yaml(source_path)
    if key not in source_data:
        raise KeyError(f"Key '{key}' not found in {source_path}")
    return source_data[key]

def update_target_yaml(target_path, target_keys, new_value):
    """Update specified keys in the target YAML file with the new value."""
    target_data = load_yaml(target_path)
    updated = False
    for key in target_keys:
        if key in target_data:
            # Update the value, preserving the key's position
            target_data[key] = float(new_value) if key == TARGET_KEYS[0] else -float(new_value)
            updated = True
        else:
            print(f"Warning: Key '{key}' not found in {target_path}")
    if updated:
        save_yaml(target_data, target_path)
    else:
        print(f"No updates made to {target_path}")

def main():
    """Main function to execute the YAML update process."""
    start_time = time.time()
    
    # Resolve absolute paths
    source_path = PROJECT_ROOT / SOURCE_CONFIG_PATH
    target_path = PROJECT_ROOT / TARGET_CONFIG_PATH
    
    try:
        # Get the value from source YAML
        new_value = get_source_value(source_path, SOURCE_KEY)
        
        # Update the target YAML
        update_target_yaml(target_path, TARGET_KEYS, new_value)
        
        # Calculate and display execution time
        execution_time = time.time() - start_time
        print(f"- - A - - Successfully updated")
        # print(f"Script execution time: {execution_time:.4f} seconds")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()


