import os
from ruamel.yaml import YAML

# Settings
INPUT_FILE = 'CORE/DATA/A_candle.yaml'
CLOSE_KEY = 'CLOSE_PRICE'
OPEN_KEY = 'OPEN_PRICE'

OUTPUT_FILE = 'CORE/DATA/triggers_config.yaml'
PERCENT_KEY = 'PERCENT_STATUS'

OUTPUT_DIR = 'CORE/BACKEND/B_CREATE_DATA'
ROUND_DIGITS = 3

# Init ruamel.yaml
yaml = YAML()
yaml.preserve_quotes = True  # Preserve quotes style

# Read input data
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = yaml.load(f)

close = None
open_val = None

# Extract open and close from nested structure
for symbol_key, symbol_data in data.items():
    if isinstance(symbol_data, dict):
        if CLOSE_KEY in symbol_data:
            close = float(symbol_data[CLOSE_KEY])
        if OPEN_KEY in symbol_data:
            open_val = float(symbol_data[OPEN_KEY])
        
        # If we found both values, we can break
        if close is not None and open_val is not None:
            break

if close is None or open_val is None:
    raise ValueError(f"Keys '{CLOSE_KEY}' or '{OPEN_KEY}' not found in input file.")

# Calculate percent
if close != open_val:
    percent = ((close - open_val) / open_val) * 100
    new_percent = round(percent, ROUND_DIGITS)
else:
    print("Close price equals open price, no percentage change.")
    exit()

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read existing output file to preserve formatting/comments
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        output_data = yaml.load(f)
else:
    output_data = {}

# Update percent
output_data[PERCENT_KEY] = new_percent

# Save changes preserving formatting
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    yaml.dump(output_data, f)

# print(f"Calculated percentage change: {new_percent}%")
