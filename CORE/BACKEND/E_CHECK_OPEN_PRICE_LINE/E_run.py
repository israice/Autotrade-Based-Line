import time
import subprocess
import os
from pathlib import Path

# List of scripts to execute
SCRIPTS = [
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/EA_create_SMALL_OPEN_STATUS.py',
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/EB_check_end_of_open_cross.py',
    'CORE/BACKEND/E_CHECK_OPEN_PRICE_LINE/EC_check_start_of_open_cross.py',
]

def main():
    # Get project root (where .env file is located)
    project_root = Path(__file__).parent
    while not (project_root / '.env').exists():
        project_root = project_root.parent
        if project_root == project_root.parent:  # Reached filesystem root
            raise FileNotFoundError(".env file not found in project hierarchy")

    # Measure start time
    start_time = time.time()

    # Execute each script
    for script_path in SCRIPTS:
        full_path = project_root / script_path
        if not full_path.exists():
            print(f"Error: Script not found at {full_path}")
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
                    print(line.strip())

            # Print stderr if it exists
            for line in result.stderr.splitlines():
                if line.strip():
                    print(f"Error: {line.strip()}")

        except subprocess.CalledProcessError as e:
            print(f"Error executing {script_path}: {e}")
        except Exception as e:
            print(f"Unexpected error executing {script_path}: {e}")

    # Calculate and display execution time
    execution_time = time.time() - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()