import yaml
import subprocess
from operator import gt, lt, ge, le, eq, ne

# Configuration and paths
DATA_FILE = "CORE/DATA/AA_CANDLE.yaml"
SCRIPTS = [
    "TOOLS/message_checked.py",
    # "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FA_if_candle_not_ended.py",
]

# Candle key names
CANDLE_0_HIGH = "candle_0_high"
HIGH_COMPARISON = ">"  # Options: >, <, >=, <=, ==, !=
CANDLE_1_HIGH = "candle_1_high"
# Candle key names
CANDLE_0_LOW = "candle_0_low"
LOW_COMPARISON = "<"   # Options: >, <, >=, <=, ==, !=
CANDLE_1_LOW = "candle_1_low"

# Mapping string operators to functions
OPERATOR_MAP = {
    ">": gt,
    "<": lt,
    ">=": ge,
    "<=": le,
    "==": eq,
    "!=": ne
}

# Load YAML file
with open(DATA_FILE, 'r') as file:
    data = yaml.safe_load(file)

# Extract candle data
candle_0 = data[0]
candle_1 = data[1]

# Get comparison functions
high_op = OPERATOR_MAP[HIGH_COMPARISON]
low_op = OPERATOR_MAP[LOW_COMPARISON]

# Compare high and low values
if (high_op(float(candle_0[CANDLE_0_HIGH]), float(candle_1[CANDLE_1_HIGH])) or
    low_op(float(candle_0[CANDLE_0_LOW]), float(candle_1[CANDLE_1_LOW]))):
    
    # Run scripts sequentially
    for script in SCRIPTS:
        subprocess.run(['python', script])