import yaml
import time
from pathlib import Path

# Configuration
INPUT_FILE = Path("CORE/DATA/B_large_new_candles_data.yaml")
OUTPUT_FILE = Path("CORE/DATA/C_temp_config.yaml")
CANDLE_HIGH_KEY = "candle_1_high"
CANDLE_LOW_KEY = "candle_1_low"
CONFIG_HIGH_KEY = "HIGH_PRICE"
CONFIG_LOW_KEY = "LOW_PRICE"

# Start timing
start_time = time.time()

# Read input YAML file
try:
    with open(INPUT_FILE, 'r') as file:
        data = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Error: Input file {INPUT_FILE} not found")
    exit(1)

# Extract candle_1_high and candle_1_low
candle_data = next((item for item in data if CANDLE_HIGH_KEY in item and CANDLE_LOW_KEY in item), None)
if not candle_data:
    print(f"Error: {CANDLE_HIGH_KEY} or {CANDLE_LOW_KEY} not found in {INPUT_FILE}")
    exit(1)

high_price = candle_data[CANDLE_HIGH_KEY]
low_price = candle_data[CANDLE_LOW_KEY]

# Read output YAML file content
try:
    with open(OUTPUT_FILE, 'r') as file:
        lines = file.readlines()
except FileNotFoundError:
    print(f"Error: Output file {OUTPUT_FILE} not found")
    exit(1)

# Update specific lines
updated_lines = []
high_updated = False
low_updated = False

for line in lines:
    stripped_line = line.strip()
    if stripped_line.startswith(f"{CONFIG_HIGH_KEY}:"):
        updated_lines.append(f"{CONFIG_HIGH_KEY}: {high_price}\n")
        high_updated = True
    elif stripped_line.startswith(f"{CONFIG_LOW_KEY}:"):
        updated_lines.append(f"{CONFIG_LOW_KEY}: {low_price}\n")
        low_updated = True
    else:
        updated_lines.append(line)

# Check if both keys were found and updated
if not high_updated or not low_updated:
    print(f"Error: Could not find {CONFIG_HIGH_KEY} or {CONFIG_LOW_KEY} in {OUTPUT_FILE}")
    exit(1)

# Write updated content back to output file
with open(OUTPUT_FILE, 'w') as file:
    file.writelines(updated_lines)

# Calculate and print execution time
execution_time = time.time() - start_time
# print(f"Script executed successfully in {execution_time:.4f} seconds")