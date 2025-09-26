import re

# ================== CONFIGURATION ==================
CONFIG_FILE = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"  # use forward slashes
TARGET_KEY = "COUNT_1m_INSIDE_1d_OPEN_LINE"
FROM_VALUE = "0"   # replace only if current value is exactly 0 / '0' / "0"
TO_VALUE = "1"     # new value
# ===================================================

def replace_zero_with_one(file_path: str, key: str, from_value: str, to_value: str) -> bool:
    """
    Replace YAML value for 'key' with 'to_value' ONLY if it equals 'from_value'.
    - Preserves indentation and trailing comments.
    - Preserves original line endings and does NOT add a blank line at EOF.
    """
    try:
        # Read preserving original newlines
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            lines = f.read().splitlines(keepends=True)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return False
    except Exception as e:
        print(f"Error: Failed to read {file_path}: {e}")
        return False

    key_re = re.compile(rf'^(\s*){re.escape(key)}\s*:\s*')
    zero_re = re.compile(
        rf'^(\s*){re.escape(key)}\s*:\s*(?P<q>["\']?){re.escape(from_value)}(?P=q)(?P<trail>\s*(#.*)?)\s*$'
    )

    found = False
    changed = False

    for i, raw_line in enumerate(lines):
        # Separate content and its original EOL to preserve it
        line_no_eol = raw_line.rstrip("\r\n")
        eol = raw_line[len(line_no_eol):]  # '', '\n', or '\r\n'

        if not key_re.match(line_no_eol):
            continue

        found = True
        m = zero_re.match(line_no_eol)
        if m:
            indent = m.group(1) or ""
            trail = m.group("trail") or ""
            # Write replacement keeping original EOL (no extra blank line)
            lines[i] = f"{indent}{key}: {to_value}{trail}{eol}"
            changed = True
        break  # stop at first occurrence

    if not found:
        print(f"Error: Key {key} not found in {file_path}")
        return False

    if changed:
        try:
            # Write back exactly what we built (no newline normalization)
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Error: Failed to update {file_path}: {e}")
            return False

    return True

# ====================== LOGIC =======================
if not replace_zero_with_one(CONFIG_FILE, TARGET_KEY, FROM_VALUE, TO_VALUE):
    exit(1)
