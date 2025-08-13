import contextlib
import io

SCRIPTS = [
    "TOOLS/DISABLE_FLOW_1.py",
    # ########### RESET CANDLE ##############
    "TOOLS/RESET_CANDLE_DATA_FILES.py",
    "TOOLS/GET_FIRST_CANDLE.py",
    "TOOLS/COPY_CANDLES.py",
    # ########### RESET DB ##################
    "TOOLS/RESET_DB.py",
    "TOOLS/GET_SECOND_CANDLES_ADD_TO_DB.py",
    "TOOLS/DELAY_BY_SETTINGS.py",
    # #######################################
    "TOOLS/ENABLE_FLOW_1.py",
    # "TOOLS/create_ORDER_SYMBOL.py", 
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
]

for script_path in SCRIPTS:
    # Read the script code
    with open(script_path, 'r') as f:
        code = f.read()
    
    # Prepare to capture output
    output_capture = io.StringIO()
    
    # Redirect stdout and execute the code
    with contextlib.redirect_stdout(output_capture):
        exec(code)
    
    # Get the captured output
    captured_output = output_capture.getvalue()
    
    # Remove empty lines
    lines = [line for line in captured_output.splitlines() if line.strip()]
    filtered_output = '\n'.join(lines)
    
