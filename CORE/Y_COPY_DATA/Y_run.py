import os
import subprocess
import time
from pathlib import Path

# List of scripts to run
SCRIPTS = [
    'CORE/Y_COPY_DATA/YA_clone_candles.py',
]

def run_scripts():
    # Get the project root directory (where .env is located)
    project_root = Path(__file__).parent
    while not (project_root / '.env').exists() and project_root != project_root.parent:
        project_root = project_root.parent
    
    start_time = time.time()
    
    for script in SCRIPTS:
        script_path = project_root / script
        if not script_path.exists():
            print(f"Error: Script {script} not found")
            continue
            
        try:
            # Run script and capture output
            process = subprocess.run(
                ['python', str(script_path)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Print non-empty output lines
            output = process.stdout.strip()
            if output:
                print(output)
                
            # Print non-empty error lines
            error = process.stderr.strip()
            if error:
                print(error)
                
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e.stderr.strip()}")
            
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    run_scripts()