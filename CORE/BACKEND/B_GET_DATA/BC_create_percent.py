import yaml
import time
from pathlib import Path
from typing import Dict, Any

# Configuration variables
CONFIG_FILE_PATH = "CORE/DATA/C_temp_config.yaml"
SMALL_CANDLES_FILE_PATH = "CORE/DATA/A_small_new_candles_data.yaml"
LARGE_CANDLES_FILE_PATH = "CORE/DATA/B_large_new_candles_data.yaml"
SMALL_OPEN_CHANGE_KEY = "SMALL_OPEN_CHANGE"
LARGE_OPEN_CHANGE_KEY = "LARGE_OPEN_CHANGE"
LARGE_OPEN_STATUS_KEY = "LARGE_OPEN_STATUS"
CANDLE_OPEN_KEY = "candle_0_open"
CANDLE_CLOSE_KEY = "candle_0_close"
RED_STATUS = "RED"
GREEN_STATUS = "GREEN"

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load YAML file and return its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML file {file_path}: {e}")
        exit(1)

def save_yaml_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to YAML file while preserving structure and comments."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Read current config to get values
        config_data = yaml.safe_load(''.join(lines)) or {}
        
        # Update only the specified keys
        for key, value in data.items():
            if key in config_data:
                for i, line in enumerate(lines):
                    if line.strip().startswith(f"{key}:"):
                        # Preserve comments and indentation
                        indent = len(line) - len(line.lstrip())
                        if isinstance(value, float):
                            lines[i] = f"{' ' * indent}{key}: {value:.3f}\n"
                        else:
                            lines[i] = f"{' ' * indent}{key}: {value}\n"
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML file {file_path}: {e}")
        exit(1)

def calculate_percentage_change(open_price: str, close_price: str) -> float:
    """Calculate percentage change between open and close prices."""
    try:
        open_val = float(open_price)
        close_val = float(close_price)
        return ((close_val - open_val) / open_val) * 100
    except (ValueError, ZeroDivisionError) as e:
        print(f"Error: Invalid price values - open: {open_price}, close: {close_price}, error: {e}")
        exit(1)

def main():
    start_time = time.time()
    
    # Load candle data
    small_candles_data = load_yaml_file(SMALL_CANDLES_FILE_PATH)
    large_candles_data = load_yaml_file(LARGE_CANDLES_FILE_PATH)
    
    # Check if required candle data exists
    if not small_candles_data or not isinstance(small_candles_data, list) or not small_candles_data[0]:
        print(f"Error: Invalid or empty data in {SMALL_CANDLES_FILE_PATH}")
        exit(1)
    if not large_candles_data or not isinstance(large_candles_data, list) or not large_candles_data[0]:
        print(f"Error: Invalid or empty data in {LARGE_CANDLES_FILE_PATH}")
        exit(1)
    
    # Get candle values
    small_open = small_candles_data[0].get(CANDLE_OPEN_KEY)
    small_close = small_candles_data[0].get(CANDLE_CLOSE_KEY)
    large_open = large_candles_data[0].get(CANDLE_OPEN_KEY)
    large_close = small_candles_data[0].get(CANDLE_CLOSE_KEY)
    
    # Validate candle values
    for key, value in [
        (CANDLE_OPEN_KEY, small_open),
        (CANDLE_CLOSE_KEY, small_close),
        (CANDLE_OPEN_KEY, large_open),
        (CANDLE_CLOSE_KEY, large_close)
    ]:
        if not value:
            print(f"Error: Missing {key} in candle data")
            exit(1)
    
    # Calculate changes
    small_change = calculate_percentage_change(small_open, small_close)
    large_change = calculate_percentage_change(large_open, large_close)
    
    # Prepare config update
    config_update = {
        SMALL_OPEN_CHANGE_KEY: small_change,
        LARGE_OPEN_CHANGE_KEY: large_change
    }
    
    # Update status only if large change is not zero
    if large_change != 0:
        config_update[LARGE_OPEN_STATUS_KEY] = RED_STATUS if large_change < 0 else GREEN_STATUS
    
    # Save updated config
    save_yaml_file(CONFIG_FILE_PATH, config_update)
    
    end_time = time.time()
    # print(f"Script execution time: {(end_time - start_time):.4f} seconds")

if __name__ == "__main__":
    main()