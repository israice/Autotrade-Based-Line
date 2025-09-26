import yaml
import os
import sys
import time
import builtins
import subprocess
import signal
import atexit

# =========================
# Settings (configurable)
# =========================
CONFIG_PATH = 'settings.yaml'
CONFIG_HEADER = 'SYSTEM_RUN'
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_DOWN_WORD = 'DISABLE'

SCRIPTS_YES = [
    'CORE/BACKEND/A_CHECK_CONNECTION_TYPE/A_CHECK_CONNECTION_TYPE.py',
]

SCRIPTS_NO = [
]

# Output behavior
FORCE_FLUSH_PRINTS = True                   # Force flush=True for all print() inside child scripts
LINE_BUFFER_STDIO = True                    # Reconfigure sys.stdout/sys.stderr for line buffering when possible

# =========================
# Helpers (implementation)
# =========================
if LINE_BUFFER_STDIO:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

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

# =========================
# Process management
# =========================
processes = []

def cleanup():
    """Terminate all child processes on exit."""
    for p in processes:
        if p.poll() is None:  # still running
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

# Register cleanup for normal exit and signals
atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))
signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))

# =========================
# Start scripts as processes
# =========================
for script in scripts:
    if not os.path.exists(script):
        print(f"Error: Script {script} not found", flush=True)
        continue
    try:
        # Launch as independent Python process
        cmd = [sys.executable, script]
        if FORCE_FLUSH_PRINTS:
            cmd.insert(1, "-u")  # force unbuffered mode

        p = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            bufsize=1,
            universal_newlines=True
        )
        processes.append(p)

    except Exception as e:
        print(f"Error executing {script}: {e}", flush=True)

# Wait for all child processes to finish
for p in processes:
    p.wait()
