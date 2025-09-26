import yaml
import os
import sys
import time
import builtins

# =========================
# Settings (configurable)
# =========================
CONFIG_PATH = 'settings.yaml'
CONFIG_HEADER = 'SYSTEM_RUN'
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_DOWN_WORD = 'DISABLE'

SCRIPTS_YES = [
    "CORE/BACKEND/E_CHECK_OPEN_LINE_CROSS/EA_CHECK_PERCENT_VS_TREND.py", 
]

SCRIPTS_NO = [
]

# Output behavior: real-time, no buffering/memory
FORCE_FLUSH_PRINTS = True                   # Force flush=True for all print() inside child scripts
LINE_BUFFER_STDIO = True                    # Reconfigure sys.stdout/sys.stderr for line buffering when possible

# =========================
# Helpers (implementation)
# =========================
# Ensure our own stdio is as unbuffered as Python allows without proxies.
if LINE_BUFFER_STDIO:
    try:
        # Reconfigure only if available (TextIOWrapper). This keeps writes immediate on newline.
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

# Prepare a print() that always flushes (no buffering). We'll inject this for child scripts only.
_original_print = builtins.print

def _print_flush(*args, **kwargs):
    """print() wrapper that forces flush=True to avoid buffering."""
    kwargs.setdefault('flush', True)
    return _original_print(*args, **kwargs)

# =========================
# Logic (universal names)
# =========================
config_value = None
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        if config is not None:
            config_value = config.get(CONFIG_HEADER)
except FileNotFoundError:
    pass
except yaml.YAMLError:
    pass

if config_value is None:
    scripts = []
else:
    if isinstance(config_value, bool):
        config_value = SCRIPTS_UP_WORD if config_value else SCRIPTS_DOWN_WORD

    if config_value == SCRIPTS_UP_WORD:
        scripts = SCRIPTS_YES
    elif config_value == SCRIPTS_DOWN_WORD:
        scripts = SCRIPTS_NO
    else:
        print(f" - Wrong value key {config_value} for {CONFIG_HEADER}")
        sys.exit(1)

for script in scripts:
    if not os.path.exists(script):
        print(f"Error: Script {script} not found", flush=True)  # Ensure immediate visibility
        continue
    try:
        # Read and compile the script code (no accumulation of output; just code loading).
        with open(script, 'r', encoding='utf-8') as f:
            code = compile(f.read(), script, 'exec')

        # Prepare execution globals to mimic __main__
        exec_globals = {'__name__': '__main__', '__file__': script}

        # Execute child script with forced flush on all print() calls to ensure real-time output.
        if FORCE_FLUSH_PRINTS:
            builtins.print = _print_flush  # Inject flush-on-print for the duration of the child script
        try:
            exec(code, exec_globals)
        finally:
            # Always restore builtins.print even if child script fails
            builtins.print = _original_print

    except Exception as e:
        # Print errors immediately; do not buffer
        print(f"Error executing {script}: {e}", flush=True)
