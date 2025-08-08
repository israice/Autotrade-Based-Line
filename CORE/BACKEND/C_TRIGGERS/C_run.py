import yaml
import subprocess
import time
import sys

TRIGGER_KEY = "TRIGGERS"
CONFIG_FILE = "CORE/DATA/system_config.yaml"
SCRIPTS = [
    "CORE/BACKEND/C_TRIGGERS/A_CANDLE_LONG_END/A_run.py",
    "CORE/BACKEND/C_TRIGGERS/B_CANDLE_SHORT_END/B_run.py",
    "CORE/BACKEND/C_TRIGGERS/C_CANDLE_HIGH_LINE/C_run.py",
    "CORE/BACKEND/C_TRIGGERS/D_CANDLE_OPEN_LINE/D_run.py",
    "CORE/BACKEND/C_TRIGGERS/E_CANDLE_LOW_LINE/E_run.py",
    "CORE/BACKEND/C_TRIGGERS/F_CANDLE_LONG_PERCENT/F_run.py",
    "CORE/BACKEND/C_TRIGGERS/G_CANDLE_SHORT_PERCENT/G_run.py",
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
        print(f"Execution time: {end_time - start_time:.2f} seconds")
except FileNotFoundError:
    print(f"Error: {CONFIG_FILE} not found")
    sys.exit(1)
except yaml.YAMLError:
    print(f"Error: Failed to parse {CONFIG_FILE}")
    sys.exit(1)