import contextlib
import io

SCRIPTS = [
    "TOOLS/DELAY_BY_SETTINGS.py",
    # ##############################################
    # "CORE/BACKEND/B_CREATE_DATA/B_run.py",
    # "CORE/BACKEND/C_CHECK_CANDLE_END/C_if_candle_ends.py",
    # "CORE/BACKEND/D_CHECK_PERCENT_SELL/D_if_percent_positive_or_negative.py",
    # "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/E_if_trend_changes.py",
    # "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/F_if_candle_one_outside.py",
    # ##############################################
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
    
