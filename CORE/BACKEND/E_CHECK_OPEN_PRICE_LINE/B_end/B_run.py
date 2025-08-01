import os
import subprocess
import time
from pathlib import Path

SCRIPTS = [
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/B_end/BA_create_SMALL_OPEN_STATUS.py',
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/B_end/BB_check_end_of_open_cross.py',
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/B_end/BC_check_start_of_open_cross.py',
]

def run_scripts():
    start_time = time.time()
    project_root = Path.cwd()
    for script in SCRIPTS:
        script_path = project_root / script
        if script_path.exists():
            result = subprocess.run(['python', str(script_path)], capture_output=True, text=True)
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='')
        else:
            print(f"Script not found: {script_path}", end='')
    end_time = time.time()
    # print(f"Total execution time: {end_time - start_time:.2f} seconds", end='')

if __name__ == "__main__":
    run_scripts()