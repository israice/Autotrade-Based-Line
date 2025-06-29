import sys
sys.dont_write_bytecode = True
import subprocess
import time
import gc
from CORE.BACKEND.A_GET_DATA.AA_fetch_candles import load_settings

settings = load_settings()
delay = settings.get('delay')

clear_files = [
    "test1.py",
    "test2.py",
    "test3.py",
    "test4.py",
]

loop_check = [
    "CORE/BACKEND/A_GET_DATA/A_run.py",
    "CORE/BACKEND/B_CHECK_TREND/B_run.py",
    "CORE/BACKEND/Z_CLONE_CANDLE/Z_run.py"
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
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Execution time: {elapsed:.2f} seconds.")
        gc.collect() # Clear memory
        if stop_requested:
            break
        time.sleep(delay)
except Exception as e:
    print(f"Ошибка: {e}")
