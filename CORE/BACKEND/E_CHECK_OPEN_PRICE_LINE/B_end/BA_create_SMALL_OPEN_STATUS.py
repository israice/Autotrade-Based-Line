import yaml
import os

# Configuration settings
LARGE_CANDLES_FILE = "CORE/DATA/B_large_new_candles_data.yaml"
SMALL_CANDLES_FILE = "CORE/DATA/A_small_new_candles_data.yaml"
CONFIG_FILE = "CORE/DATA/C_temp_config.yaml"

# Keys to read from YAML files
OPEN_KEY = "candle_0_open"
HIGH_KEY = "candle_0_high"
LOW_KEY = "candle_0_low"

# Output key and values
OUTPUT_KEY = "SMALL_OPEN_STATUS"
CROSS_VALUE = "CROSS"
GREEN_VALUE = "GREEN"
RED_VALUE = "RED"

def load_yaml_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def write_yaml_file(file_path, data):
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file)

def update_config_file(file_path, key, value):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found")
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}:"):
            lines[i] = f"{key}: {value}\n"
            found = True
            break
    
    if not found:
        raise KeyError(f"Key {key} not found in {file_path}")
    
    with open(file_path, 'w') as file:
        file.writelines(lines)

def main():
    # Load data from YAML files
    large_data = load_yaml_file(LARGE_CANDLES_FILE)
    small_data = load_yaml_file(SMALL_CANDLES_FILE)

    # Extract values
    if not isinstance(large_data, list) or not large_data:
        raise KeyError("Invalid or empty data in large candles file")
    if not isinstance(small_data, list) or not small_data:
        raise KeyError("Invalid or empty data in small candles file")

    candle_0_large = large_data[0]
    candle_0_small = small_data[0]

    if OPEN_KEY not in candle_0_large:
        raise KeyError(f"{OPEN_KEY} not found in {LARGE_CANDLES_FILE}")
    if HIGH_KEY not in candle_0_small:
        raise KeyError(f"{HIGH_KEY} not found in {SMALL_CANDLES_FILE}")
    if LOW_KEY not in candle_0_small:
        raise KeyError(f"{LOW_KEY} not found in {SMALL_CANDLES_FILE}")

    open_price = float(candle_0_large[OPEN_KEY])
    high_price = float(candle_0_small[HIGH_KEY])
    low_price = float(candle_0_small[LOW_KEY])

    # Determine status
    if high_price >= open_price and low_price <= open_price:
        status = CROSS_VALUE
    elif high_price > open_price and low_price > open_price:
        status = GREEN_VALUE
    elif high_price < open_price and low_price < open_price:
        status = RED_VALUE
    else:
        raise ValueError("Invalid price comparison condition")

    # Update config file
    update_config_file(CONFIG_FILE, OUTPUT_KEY, status)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")