import contextlib
import io

SCRIPTS = [
    "CORE/BACKEND/A_START/A_RUN_LIST.py",
    "CORE/BACKEND/Z_END/Z_RUN_LIST.py",
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
    
