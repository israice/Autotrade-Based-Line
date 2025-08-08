import yaml
import subprocess

# Load config.yaml
with open('CORE/DATA/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
high_line = config['HIGH_LINE']
low_line = config['LOW_LINE']

# Load candle data
with open('CORE/DATA/A_candle.yaml', 'r') as f:
    data = yaml.safe_load(f)
candle_0 = data[0]
candle_1 = data[1]

# Convert prices to floats
close0 = float(candle_0['candle_0_close'])
open0 = float(candle_0['candle_0_open'])
high1 = float(candle_1['candle_1_high'])
low1 = float(candle_1['candle_1_low'])

# First condition
if close0 > open0:
    if close0 > high1:
        if high_line != 'UP':
            scripts = [
                'CORE/D_CHECK_HIGH_LOW_LINE/DA_check_high_up.py',
            ]
            for script in scripts:
                subprocess.call(['python', script])

# Second condition
if close0 > open0:
    if close0 < high1:
        if high_line != 'DOWN':
            scripts = [
                'CORE/D_CHECK_HIGH_LOW_LINE/DB_check_high_down.py',
            ]
            for script in scripts:
                subprocess.call(['python', script])

# Third condition
if close0 < open0:
    if close0 > low1:
        if low_line != 'UP':
            scripts = [
                'CORE/D_CHECK_HIGH_LOW_LINE/DC_check_low_up.py',
            ]
            for script in scripts:
                subprocess.call(['python', script])

# Fourth condition
if close0 < open0:
    if close0 < low1:
        if low_line != 'DOWN':
            scripts = [
                'CORE/D_CHECK_HIGH_LOW_LINE/DD_check_low_down.py',
            ]
            for script in scripts:
                subprocess.call(['python', script])