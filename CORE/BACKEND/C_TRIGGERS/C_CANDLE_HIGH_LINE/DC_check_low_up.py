import yaml
import subprocess

# Configuration
CONFIG_FILE = "CORE/DATA/system_config.yaml"
KEY_LOW_LINE = "LOW_LINE"
KEY_LOW_COUNTER = "LOW_COUNTER"
VALUE_DOWN = "DOWN"
VALUE_UP = "UP"
COUNTER_INCREMENT = 1
SCRIPTS = [
    "CORE/BACKEND/D_CHECK_HIGH_LOW_LINE/DCA_message_low_up.py",
    "CORE/BACKEND/Z_TOOLS/order_buy_long.py",
    # "CORE/BACKEND/Z_TOOLS/order_sell_short.py",
    # "CORE/BACKEND/Z_TOOLS/add_NOW_AMOUNT.py",
]

def read_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def write_yaml(file_path, data):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Keep track of whether we found the keys
    found_low_line = False
    found_low_counter = False
    
    # Update specific values while preserving order and comments
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{KEY_LOW_LINE}:"):
            lines[i] = f"{KEY_LOW_LINE}: {VALUE_UP}\n"
            found_low_line = True
        elif line.strip().startswith(f"{KEY_LOW_COUNTER}:"):
            current_value = int(line.split(':')[1].strip())
            lines[i] = f"{KEY_LOW_COUNTER}: {current_value + COUNTER_INCREMENT}\n"
            found_low_counter = True
    
    if not found_low_line:
        print(f"Error: {KEY_LOW_LINE} not found in {CONFIG_FILE}")
        return
    if not found_low_counter:
        print(f"Error: {KEY_LOW_COUNTER} not found in {CONFIG_FILE}")
        return
    
    with open(file_path, 'w') as file:
        file.writelines(lines)

def run_scripts():
    for script in SCRIPTS:
        subprocess.run(["python", script])

# Main logic
def main():
    config = read_yaml(CONFIG_FILE)
    
    if config.get(KEY_LOW_LINE) == VALUE_DOWN:
        write_yaml(CONFIG_FILE, config)
        run_scripts()

if __name__ == "__main__":
    main()