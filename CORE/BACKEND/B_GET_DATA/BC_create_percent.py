import yaml
import time
import sys
from pathlib import Path

# Configuration settings
CONFIG_FILE_PATH = "CORE/DATA/C_temp_config.yaml"
SMALL_CANDLES_FILE_PATH = "CORE/DATA/A_small_new_candles_data.yaml"
LARGE_CANDLES_FILE_PATH = "CORE/DATA/B_large_new_candles_data.yaml"
PERCENTAGE_CHANGE_LARGE_KEY = "PERCENTAGE_CHANGE_LARGE"
TREND_LARGE_KEY = "TREND_LARGE"
PERCENTAGE_CHANGE_SMALL_KEY = "PERCENTAGE_CHANGE_SMALL"
TREND_SMALL_KEY = "TREND_SMALL"
CANDLE_OPEN_KEY = "candle_0_open"
CANDLE_CLOSE_KEY = "candle_0_close"
POSITIVE_TREND = "GREEN"
NEGATIVE_TREND = "RED"

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse {file_path}: {e}")
        sys.exit(1)

def calculate_percentage_change(open_price, close_price):
    try:
        open_val = float(open_price)
        close_val = float(close_price)
        if open_val == 0:
            return 0.0
        percentage_change = ((close_val - open_val) / open_val) * 100
        return round(percentage_change, 3)
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid price values - open: {open_price}, close: {close_price}: {e}")
        sys.exit(1)

def get_trend(percentage_change):
    if percentage_change > 0:
        return POSITIVE_TREND
    elif percentage_change < 0:
        return NEGATIVE_TREND
    return None

def update_config_file(config_path, updates):
    try:
        with open(config_path, 'r') as file:
            lines = file.readlines()
        
        updated_lines = lines.copy()
        for key, value in updates.items():
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}:"):
                    indent = line[:line.find(key)]
                    updated_lines[i] = f"{indent}{key}: {value}\n"
                    break
        
        with open(config_path, 'w') as file:
            file.writelines(updated_lines)
    except FileNotFoundError:
        print(f"Error: Config file {config_path} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to update config file {config_path}: {e}")
        sys.exit(1)

def main():
    start_time = time.time()
    
    # Load candle data
    small_candles_data = load_yaml_file(SMALL_CANDLES_FILE_PATH)
    large_candles_data = load_yaml_file(LARGE_CANDLES_FILE_PATH)
    
    # Get small candle values
    small_open = small_candles_data[0].get(CANDLE_OPEN_KEY)
    small_close = small_candles_data[0].get(CANDLE_CLOSE_KEY)
    if small_open is None or small_close is None:
        print(f"Error: Missing {CANDLE_OPEN_KEY} or {CANDLE_CLOSE_KEY} in {SMALL_CANDLES_FILE_PATH}")
        sys.exit(1)
    
    # Get large candle open value
    large_open = large_candles_data[0].get(CANDLE_OPEN_KEY)
    if large_open is None:
        print(f"Error: Missing {CANDLE_OPEN_KEY} in {LARGE_CANDLES_FILE_PATH}")
        sys.exit(1)
    
    # Calculate percentage changes
    small_percentage_change = calculate_percentage_change(small_open, small_close)
    large_percentage_change = calculate_percentage_change(large_open, small_close)
    
    # Determine trends
    small_trend = get_trend(small_percentage_change)
    large_trend = get_trend(large_percentage_change)
    
    # Prepare updates
    updates = {
        PERCENTAGE_CHANGE_SMALL_KEY: f"{small_percentage_change:.3f}%",
        PERCENTAGE_CHANGE_LARGE_KEY: f"{large_percentage_change:.3f}%"
    }
    
    # Only update trends if percentage change is not zero
    if small_trend and small_percentage_change != 0:
        updates[TREND_SMALL_KEY] = small_trend
    if large_trend and large_percentage_change != 0:
        updates[TREND_LARGE_KEY] = large_trend
    
    # Update config file
    update_config_file(CONFIG_FILE_PATH, updates)
    
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"Script execution time: {execution_time:.3f} seconds")

if __name__ == "__main__":
    main()