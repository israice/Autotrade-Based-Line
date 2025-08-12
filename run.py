import os
import sys
import subprocess
import time
import signal
import threading

PRE_CONFIG = [
    "TOOLS/reset_db.py",
    "TOOLS/reset_candle_data_files.py",
    "TOOLS/get_second_candles_add_to_db.py",
    # ##############################################
    # "TOOLS/create_ORDER_SYMBOL.py", 
    # "TOOLS/binance_two_candles.py",
    # "TOOLS/reset_COUNTER_HIGH_CROSSING.py",
    # "TOOLS/reset_COUNTER_OPEN_CROSSING.py",
    # "TOOLS/reset_COUNTER_LOW_CROSSING.py",
    # "TOOLS/reset_PERCENT_SELL.py",
    # "TOOLS/reset_TREND_STATUS.py",
    # "TOOLS/enable_CROSSING_UP_GREEN.py",
    # "TOOLS/disable_CROSSING_DOWN_GREEN.py",
    # "TOOLS/disable_CROSSING_UP_RED.py",
    # "TOOLS/enable_CROSSING_DOWN_RED.py",
    # "TOOLS/create_ORDER_ACCOUNT_ID.py",
    # 'TOOLS/binance_info_for_order_budy.py',
    # 'TOOLS/clone_candles.py',
    # ##############################################
    "TOOLS/binance_websocket_stream.py",
]

MAIN_SCRIPTS_LIST = [
    "TOOLS/DELAY_BY_SETTINGS.py",
    # ##############################################
    # "CORE/BACKEND/B_CREATE_DATA/B_run.py",
    # "CORE/BACKEND/C_CHECK_CANDLE_END/C_if_candle_ends.py",
    # "CORE/BACKEND/D_CHECK_PERCENT_SELL/D_if_percent_positive_or_negative.py",
    # "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/E_if_trend_changes.py",
    # "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/F_if_candle_one_outside.py",
    # ##############################################
    "TOOLS/check_for_copy_candles.py",    

]

interrupt_flag = False
running_pre = []
running_scripts = []
lock = threading.Lock()

def signal_handler(sig, frame):
    global interrupt_flag
    interrupt_flag = True
    with lock:
        for p in running_pre[:]:
            try:
                p.terminate()
            except:
                pass

signal.signal(signal.SIGINT, signal_handler)

if sys.platform == "win32":
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
else:
    creation_flags = 0

def run_script(script, is_pre=False):
    p = subprocess.Popen([sys.executable, script], creationflags=creation_flags)
    with lock:
        if is_pre:
            running_pre.append(p)
        else:
            running_scripts.append(p)
    try:
        p.wait()
    finally:
        with lock:
            if is_pre:
                if p in running_pre:
                    running_pre.remove(p)
            else:
                if p in running_scripts:
                    running_scripts.remove(p)
    return p.returncode

def run_pre_config():
    for script in PRE_CONFIG:
        run_script(script, is_pre=True)

# Start PRE_CONFIG in a separate thread
pre_thread = threading.Thread(target=run_pre_config)
pre_thread.start()

# Run MAIN_SCRIPTS_LIST in a loop in the main thread
while True:
    if interrupt_flag:
        break
    start_time = time.time()
    for script in MAIN_SCRIPTS_LIST:
        run_script(script, is_pre=False)
    end_time = time.time()
    print(f" - Execution time: {end_time - start_time:.3f} seconds ✔️")

print("Interrupted by user. Exiting...")
pre_thread.join()
