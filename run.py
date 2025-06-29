import sys
sys.dont_write_bytecode = True
import subprocess
import time
import gc

files = [
    "CHECK_CHANGE/AA_fetch_candles.py",
    "CHECK_CHANGE/AB_check_trend.py",
    "CHECK_CHANGE/AC_use_trend.py",
    "CHECK_CHANGE/ZZ_clone_candles.py"
]

from CHECK_CHANGE.AA_fetch_candles import load_settings
import yaml

settings = load_settings()
delay = settings.get('delay')

try:
    while True:
        start_time = time.time()
        for file in files:
            subprocess.run(["python", file], check=True)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Execution time: {elapsed:.2f} seconds.")
        gc.collect() # Clear memory
        time.sleep(delay)
except KeyboardInterrupt:
    pass
