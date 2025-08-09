import subprocess
import time
import yaml
import signal
import sys

# Easy configurable settings
SETTINGS_FILE = 'CORE/DATA/user_settings.yaml'

ON_START_SCRIPTS = [
    "CORE/BACKEND/A_CLEAR_ON_RUN/A_run.py"
]

MAIN_SCRIPTS = [
    "CORE/BACKEND/B_GET_DATA/B_run.py",
    "CORE/BACKEND/C_CHECK_CANDLE_END/C_if_candle_ends_then_check.py",
    "CORE/BACKEND/D_CHECK_PERCENT_SELL/D_if_percent_positive_or_negative.py",
    "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/E_if_trend_changes_then_order.py",
    "CORE/BACKEND/Y_COPY_DATA/Y_run.py",    
]

# Load settings
with open(SETTINGS_FILE, 'r') as f:
    settings = yaml.safe_load(f)

# logic
def run_script_list(scripts, measure_time=True):
    """Run list of scripts sequentially"""
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
    """Handle Ctrl+C interrupt"""
    global interrupted
    interrupted = True
    print("- - STOP - - Interrupt received, will finish current scripts and exit.")

signal.signal(signal.SIGINT, signal_handler)

# Run initial scripts once, without timing
run_script_list(ON_START_SCRIPTS, measure_time=False)

# Continuous run without any delay
while not interrupted:
    run_script_list(MAIN_SCRIPTS)
    if interrupted:
        break

if interrupted:
    sys.exit(0)
