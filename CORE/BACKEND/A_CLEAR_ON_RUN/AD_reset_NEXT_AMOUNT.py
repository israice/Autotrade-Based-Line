import time
import ruamel.yaml
from pathlib import Path

# Configuration settings
PROJECT_ROOT = Path.cwd()  # Assumes script runs from project root where .env exists
SOURCE_YAML_PATH = "settings.yaml"
TARGET_YAML_PATH = "CORE/DATA/C_temp_config.yaml"
SOURCE_KEY = "START_AMOUNT"
TARGET_KEY = "STEP_AMOUNT_NOW"

def read_yaml_file(file_path: str) -> dict:
    """Read YAML file and return its content as a dictionary."""
    full_path = PROJECT_ROOT / file_path
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            return yaml.load(file) or {}
    except FileNotFoundError:
        print(f"Error: File {full_path} not found")
        return {}
    except Exception as e:
        print(f"Error reading {full_path}: {e}")
        return {}

def write_yaml_file(file_path: str, data: dict) -> None:
    """Write data to YAML file while preserving structure."""
    full_path = PROJECT_ROOT / file_path
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file)
    except Exception as e:
        print(f"Error writing to {full_path}: {e}")

def update_yaml_value():
    """Update STEP_AMOUNT_NOW in target YAML with START_AMOUNT from source YAML."""
    start_time = time.time()
    
    # Read source YAML
    source_data = read_yaml_file(SOURCE_YAML_PATH)
    if not source_data or SOURCE_KEY not in source_data:
        print(f"Error: {SOURCE_KEY} not found in {SOURCE_YAML_PATH}")
        return
    
    source_value = source_data[SOURCE_KEY]
    
    # Read target YAML
    target_data = read_yaml_file(TARGET_YAML_PATH)
    if not target_data:
        print(f"Error: Unable to read {TARGET_YAML_PATH}")
        return
    
    # Update target value
    target_data[TARGET_KEY] = source_value
    
    # Write updated data back to target YAML
    write_yaml_file(TARGET_YAML_PATH, target_data)
    
    end_time = time.time()
    execution_time = end_time - start_time
    print("- - A - - Candles amount reset")
    print(f"Script execution time: {execution_time:.4f} seconds")

if __name__ == "__main__":
    update_yaml_value()


