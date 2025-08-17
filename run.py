import yaml
import os
import sys
import time

# =========================
# Settings (configurable)
# =========================
CONFIG_PATH = 'CORE/DATA/BB_USER_SETTINGS.yaml'
CONFIG_HEADER = 'SYSTEM_RUN'
SCRIPTS_UP_WORD = 'ENABLE'
SCRIPTS_DOWN_WORD = 'DISABLE'

SCRIPTS_YES = [
    'CORE/BACKEND/A_CHOOSE_FLOW.py',
]

SCRIPTS_NO = [
]

# Output control for child scripts (kept from previous fix)
LIMIT_EXTRA_BLANK_LINES = True               # Enable/disable blank-line filtering for child scripts
MAX_CONSECUTIVE_BLANK_LINES = 1              # Allow at most N consecutive blank/whitespace-only lines (0 = remove all)
TREAT_WHITESPACE_ONLY_AS_BLANK = True        # Treat lines with only spaces/tabs as blank
FILTER_STDERR_TOO = True                     # Also filter stderr produced by child scripts

# Final line control: avoid extra blank line after execution time print
# Set to '' to avoid trailing newline, or '\n' to keep a newline.
EXECUTION_TIME_PRINT_END = ''                # '' => no extra newline after the message

# =========================
# Helpers (implementation)
# =========================
class BlankLineLimiter:
    """Proxy stream that limits consecutive blank (or whitespace-only) lines.
    Works line-by-line, buffering until a newline is seen.
    """
    def __init__(self, stream, max_blank=1, treat_ws_blank=True):
        self._stream = stream
        self._max_blank = max_blank
        self._treat_ws_blank = treat_ws_blank
        self._blank_count = 0

    def _emit_line(self, text, ends_with_nl=True):
        # Determine if the visual line is blank
        is_blank = (text.strip() == '') if self._treat_ws_blank else (text == '')
        if ends_with_nl:
            if is_blank:
                if self._blank_count < self._max_blank:
                    self._stream.write('\n')
                self._blank_count += 1
            else:
                self._stream.write(text + '\n')
                self._blank_count = 0
        else:
            # No newline: just passthrough
            self._stream.write(text)

    def write(self, s):
        if not isinstance(s, str):
            s = str(s)
        # Normalize CRLF/CR to LF
        s = s.replace('\r\n', '\n').replace('\r', '\n')
        while s:
            nl = s.find('\n')
            if nl == -1:
                # No full line: pass through as partial
                self._stream.write(s)
                break
            # Emit complete line (without the '\n', but we add one)
            self._emit_line(s[:nl], ends_with_nl=True)
            s = s[nl + 1:]

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)

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

start_time = time.time()

for script in scripts:
    if not os.path.exists(script):
        print(f"Error: Script {script} not found")
        continue
    try:
        # Read the script code
        with open(script, 'r', encoding='utf-8') as f:
            code = compile(f.read(), script, 'exec')

        # Prepare execution globals to mimic __main__
        exec_globals = {'__name__': '__main__', '__file__': script}

        # Wrap stdout/stderr for child script output, if enabled
        if LIMIT_EXTRA_BLANK_LINES:
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            sys.stdout = BlankLineLimiter(original_stdout,
                                          max_blank=MAX_CONSECUTIVE_BLANK_LINES,
                                          treat_ws_blank=TREAT_WHITESPACE_ONLY_AS_BLANK)
            if FILTER_STDERR_TOO:
                sys.stderr = BlankLineLimiter(original_stderr,
                                              max_blank=MAX_CONSECUTIVE_BLANK_LINES,
                                              treat_ws_blank=TREAT_WHITESPACE_ONLY_AS_BLANK)
            try:
                exec(code, exec_globals)
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
        else:
            exec(code, exec_globals)

    except Exception as e:
        print(f"Error executing {script}: {e}")

end_time = time.time()
execution_time = end_time - start_time
formatted_time = f"{execution_time:.3f}"
if formatted_time != "0.000":
    # Print without trailing newline to avoid a visible blank line after this message
    print(f"- Execution time: {formatted_time} seconds ✔️", end=EXECUTION_TIME_PRINT_END)
    sys.stdout.flush()
