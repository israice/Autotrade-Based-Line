import os
import subprocess
import time
from pathlib import Path

# List of scripts to run
SCRIPTS = [
    'CORE/BACKEND/A_CLEAR_ON_RUN/AA_reset_clone_candles_file.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AB_get_large_candles.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AC_reset_NEXT_PERCENT.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AD_reset_NEXT_AMOUNT.py',
]

def run_scripts():
    # Record start time
    start_time = time.time()
    
    # Get project root directory (where .env file is located)
    project_root = Path(__file__).parent
    while not (project_root / '.env').exists():
        project_root = project_root.parent
        if project_root == project_root.parent:  # Reached filesystem root
            raise FileNotFoundError(".env file not found in project directory or its parents")
    
    # Run each script
    for script_path in SCRIPTS:
        full_path = project_root / script_path
        if not full_path.exists():
            print(f"Error: Script {script_path} not found")
            continue
            
        try:
            # Run script and capture output
            result = subprocess.run(
                ['python', str(full_path)],
                capture_output=True,
                text=True,
                check=True
            )
            # Print non-empty output lines
            for line in result.stdout.splitlines():
                if line.strip():
                    print(line)
                    
        except subprocess.CalledProcessError as e:
            print(f"Error running {script_path}: {e.stderr}")
    
    # Calculate and display execution time
    execution_time = time.time() - start_time
    # print(f"- A - - Total execution time: {execution_time:.2f} seconds")

if __name__ == '__main__':
    run_scripts()