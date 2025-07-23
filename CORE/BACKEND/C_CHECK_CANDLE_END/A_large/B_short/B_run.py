import os
import subprocess
import time
from pathlib import Path

# List of scripts to execute
SCRIPTS = [
    'CORE/BACKEND/1_TOOLS/reset_next_percent.py',
    'CORE/BACKEND/C_CHECK_CANDLE_END/A_large/B_short/BA_sell_short_order.py',
]

def run_scripts():
    # Get the project root (where .env is located)
    project_root = Path.cwd()
    while not (project_root / '.env').exists():
        project_root = project_root.parent
        if project_root == project_root.parent:  # Reached filesystem root
            raise FileNotFoundError(".env file not found in any parent directory")

    # Measure start time
    start_time = time.time()

    # Execute each script
    for script_path in SCRIPTS:
        full_path = project_root / script_path
        if not full_path.exists():
            print(f"Script not found: {full_path}")
            continue
        
        try:
            # Run the script and capture output
            result = subprocess.run(
                ['python', str(full_path)],
                capture_output=True,
                text=True,
                check=True
            )
            # Print output without adding extra newlines
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='')
        except subprocess.CalledProcessError as e:
            print(f"Error running {script_path}: {e.stderr}", end='')
        except Exception as e:
            print(f"Unexpected error running {script_path}: {str(e)}", end='')

    # Calculate and display execution time
    execution_time = time.time() - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == '__main__':
    run_scripts()