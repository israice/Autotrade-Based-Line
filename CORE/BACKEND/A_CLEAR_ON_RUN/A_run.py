import os
import time
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# List of scripts to execute
SCRIPTS = [
    'CORE/BACKEND/A_CLEAR_ON_RUN/AA_reset_clone_candles_file.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AB_get_large_candles.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AC_reset_CANDLE_PERCENT_NEXT.py',
    'CORE/BACKEND/A_CLEAR_ON_RUN/AD_reset_CANDLE_AMOUNT_NEXT.py',
]

def run_scripts():
    start_time = time.time()
    
    for script in SCRIPTS:
        script_path = os.path.join(os.getcwd(), script)
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # Execute script and capture output
        with open(script_path, 'r') as file:
            code = compile(file.read(), script_path, 'exec')
            exec(code, {})
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"- - A - - Time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    run_scripts()