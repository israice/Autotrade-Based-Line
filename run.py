import sys
sys.dont_write_bytecode = True
import subprocess
import time
import gc
from CORE.BACKEND.B_GET_DATA.BA_fetch_candles import load_settings

settings = load_settings()
delay = settings.get('delay')

clear_files = [
    "CORE/BACKEND/A_CLEAR_ON_RUN/A_run.py",
]

loop_check = [
    "CORE/BACKEND/B_GET_DATA/B_run.py",
    "CORE/BACKEND/C_CHECK_CANDLE_END/C_run.py",
    "CORE/BACKEND/Z_CLONE_CANDLE/Z_run.py",
]

import signal

stop_requested = False

def handle_sigint(signum, frame):
    global stop_requested
    stop_requested = True

signal.signal(signal.SIGINT, handle_sigint)

for test_file in clear_files:
    subprocess.run(["python", test_file], check=True)

try:
    while True:
        start_time = time.time()
        for file in loop_check:
            subprocess.run(["python", file], check=True)
        end_main = time.time()
        gc.collect() # Clear memory
        if stop_requested:
            break
        time.sleep(delay)
        end_total = time.time()
        elapsed_main = end_main - start_time
        elapsed_total = end_total - start_time
        print(f"Execution time: {elapsed_main:.2f}s (main), {elapsed_total:.2f}s (with delay)")
except Exception as e:
    pass
