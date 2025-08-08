import yaml
import subprocess
import time
import sys

TRIGGER_KEY = "TRIGGERS_CANDLE_SHORT_PERCENT"
CONFIG_FILE = "CORE/DATA/config.yaml"
SCRIPTS = [
    "CORE/BACKEND/C_TRIGGERS/A_CANDLE_LONG_END/CAA_message_up.py",
]

try:
    with open(CONFIG_FILE, 'r') as file:
        config = yaml.safe_load(file)
        if TRIGGER_KEY not in config:
            print(f"Error: {TRIGGER_KEY} not found in {CONFIG_FILE}")
            sys.exit(1)
        if config[TRIGGER_KEY] is False:
            sys.exit(0)
        start_time = time.time()
        for script in SCRIPTS:
            result = subprocess.run([sys.executable, script], capture_output=True, text=True)
            print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='')
        end_time = time.time()
        # print(f"Execution time: {end_time - start_time:.2f} seconds")
except FileNotFoundError:
    print(f"Error: {CONFIG_FILE} not found")
    sys.exit(1)
except yaml.YAMLError:
    print(f"Error: Failed to parse {CONFIG_FILE}")
    sys.exit(1)