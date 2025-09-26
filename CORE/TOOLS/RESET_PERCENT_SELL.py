import re

# Settings and configurations
file_path = 'CORE/DATA/CC_TRIGGERS_CONFIG.yaml'

long_key = 'PERCENT_LONG_SELL'
short_key = 'PERCENT_SHORT_SELL'
settings_key = 'SETTINGS_PERCENT_SELL'

# Logic
# Read the file lines
with open(file_path, 'r') as f:
    lines = f.readlines()

# Find the value of SETTINGS_PERCENT_SELL
settings_value = None
for line in lines:
    match = re.search(r'^\s*' + re.escape(settings_key) + r':\s*(-?\d+\.\d+)', line)
    if match:
        settings_value = float(match.group(1))
        break

if settings_value is None:
    raise ValueError(f"{settings_key} not found in the file")

# Determine the positive and negative values
v = abs(settings_value)
long_value = v
short_value = -v

# Prepare new lines with replacements
new_lines = []
for line in lines:
    # Replace PERCENT_LONG_SELL value if present
    if long_key + ':' in line:
        line = re.sub(r'(\s*' + re.escape(long_key) + r':\s*)(-?\d+\.\d+)', lambda m: m.group(1) + "{:.3f}".format(long_value), line)
    # Replace PERCENT_SHORT_SELL value if present
    elif short_key + ':' in line:
        line = re.sub(r'(\s*' + re.escape(short_key) + r':\s*)(-?\d+\.\d+)', lambda m: m.group(1) + "{:.3f}".format(short_value), line)
    new_lines.append(line)

# Write back to the file
with open(file_path, 'w') as f:
    f.writelines(new_lines)

