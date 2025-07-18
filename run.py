import subprocess
import time
import yaml
import signal
import sys

# Easy configurable settings
SETTINGS_FILE = 'settings.yaml'
DELAY_KEY = 'delay'

# Load settings
with open(SETTINGS_FILE, 'r') as f:
    settings = yaml.safe_load(f)

delay = settings.get(DELAY_KEY)
if delay is None:
    raise ValueError(f"{DELAY_KEY} not found in {SETTINGS_FILE}")

ON_START_SCRIPTS = [
    "CORE/BACKEND/A_CLEAR_ON_RUN/A_run.py"
]

MAIN_SCRIPTS = [
    "CORE/BACKEND/B_GET_DATA/B_run.py",
    "CORE/BACKEND/C_CHECK_CANDLE_END/C_run.py",
    "CORE/BACKEND/Z_CLONE_CANDLE/Z_run.py",
]

def run_script_list(scripts, measure_time=True):
    if measure_time:
        start_time = time.time()
    
    for script in scripts:
        proc = subprocess.Popen(['python', script], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        proc.wait()
    
    if measure_time:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for script list: {execution_time:.2f} seconds")

interrupted = False

def signal_handler(sig, frame):
    global interrupted
    interrupted = True
    print("- - STOP - - Interrupt received, will finish current scripts and exit.")

signal.signal(signal.SIGINT, signal_handler)

# Run initial scripts once, without timing
run_script_list(ON_START_SCRIPTS, measure_time=False)

while not interrupted:
    time.sleep(delay)
    run_script_list(MAIN_SCRIPTS)
    if interrupted:
        break
    time.sleep(delay)

if interrupted:
    time.sleep(0.1)
    sys.exit(0)