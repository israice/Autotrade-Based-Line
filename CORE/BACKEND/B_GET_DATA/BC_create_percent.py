import yaml
import time
import os
from pathlib import Path

# Configuration variables
CONFIG_FILE_PATH = "CORE/DATA/C_temp_config.yaml"
SMALL_CANDLES_FILE_PATH = "CORE/DATA/A_small_new_candles_data.yaml"
LARGE_CANDLES_FILE_PATH = "CORE/DATA/B_large_new_candles_data.yaml"
PERCENTAGE_CHANGE_SMALL_KEY = "PERCENTAGE_CHANGE_SMALL"
TREND_SMALL_KEY = "TREND_SMALL"
PERCENTAGE_CHANGE_LARGE_KEY = "PERCENTAGE_CHANGE_LARGE"
TREND_LARGE_KEY = "TREND_LARGE"
CANDLE_0_OPEN_KEY = "candle_0_open"
CANDLE_0_CLOSE_KEY = "candle_0_close"
GREEN = "GREEN"
RED = "RED"

# Validate file existence
def validate_file_exists(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

# Read YAML file
def read_yaml_file(file_path):
    validate_file_exists(file_path)
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Calculate percentage change
def calculate_percentage_change(open_price, close_price):
    open_price = float(open_price)
    close_price = float(close_price)
    if open_price == 0:
        return 0.0
    return ((close_price - open_price) / open_price) * 100

# Determine trend based on percentage change
def determine_trend(percentage_change):
    if percentage_change > 0:
        return GREEN
    elif percentage_change < 0:
        return RED
    return None

# Update specific keys in config file while preserving structure and comments
def update_config_file(config_file_path, updates):
    validate_file_exists(config_file_path)
    with open(config_file_path, 'r') as file:
        lines = file.readlines()
    
    updated_lines = lines.copy()
    for key, value in updates.items():
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}:"):
                # Preserve indentation and comments
                indent = line[:line.index(key)]
                updated_lines[i] = f"{indent}{key}: {value}\n"
                break
    
    with open(config_file_path, 'w') as file:
        file.writelines(updated_lines)

# Main processing function
def process_candles_data():
    start_time = time.time()
    
    # Read small candles data
    small_data = read_yaml_file(SMALL_CANDLES_FILE_PATH)
    if not small_data or not isinstance(small_data, list) or not small_data[0]:
        raise ValueError(f"Invalid data format in {SMALL_CANDLES_FILE_PATH}")
    
    small_open = small_data[0].get(CANDLE_0_OPEN_KEY)
    small_close = small_data[0].get(CANDLE_0_CLOSE_KEY)
    if small_open is None or small_close is None:
        raise KeyError(f"Missing {CANDLE_0_OPEN_KEY} or {CANDLE_0_CLOSE_KEY} in {SMALL_CANDLES_FILE_PATH}")
    
    # Calculate small candles percentage change
    small_percentage = calculate_percentage_change(small_open, small_close)
    small_updates = {PERCENTAGE_CHANGE_SMALL_KEY: f"{small_percentage:.3f}"}
    if small_percentage != 0:
        small_updates[TREND_SMALL_KEY] = determine_trend(small_percentage)
    
    # Read large candles data
    large_data = read_yaml_file(LARGE_CANDLES_FILE_PATH)
    if not large_data or not isinstance(large_data, list) or not large_data[0]:
        raise ValueError(f"Invalid data format in {LARGE_CANDLES_FILE_PATH}")
    
    large_open = large_data[0].get(CANDLE_0_OPEN_KEY)
    if large_open is None:
        raise KeyError(f"Missing {CANDLE_0_OPEN_KEY} in {LARGE_CANDLES_FILE_PATH}")
    
    # Use small candles close for large candles comparison
    large_percentage = calculate_percentage_change(large_open, small_close)
    large_updates = {PERCENTAGE_CHANGE_LARGE_KEY: f"{large_percentage:.3f}"}
    if large_percentage != 0:
        large_updates[TREND_LARGE_KEY] = determine_trend(large_percentage)
    
    # Combine updates
    updates = {**small_updates, **large_updates}
    
    # Update config file
    update_config_file(CONFIG_FILE_PATH, updates)
    
    end_time = time.time()
    # print(f"Script execution time: {end_time - start_time:.4f} seconds")

# Execute main function
try:
    process_candles_data()
except Exception as e:
    print(f"Error: {str(e)}")
    exit(1)