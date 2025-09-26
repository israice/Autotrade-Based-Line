import yaml
import os

# Configuration settings
SETTINGS_FILE = "settings.yaml"
CONFIG_FILE = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"
START_AMOUNT_KEY = "START_AMOUNT"
NOW_AMOUNT_KEY = "NOW_AMOUNT"
DECIMAL_PLACES = 3

# Logic to read, update, and write the configuration
def main():
    try:
        # Read BB_USER_SETTINGS.yaml
        if not os.path.exists(SETTINGS_FILE):
            print(f"Error: {SETTINGS_FILE} not found")
            return
        
        with open(SETTINGS_FILE, 'r') as file:
            settings = yaml.safe_load(file)
        
        if settings is None or START_AMOUNT_KEY not in settings:
            print(f"Error: {START_AMOUNT_KEY} not found in {SETTINGS_FILE}")
            return
        
        start_amount = settings[START_AMOUNT_KEY]
        
        # Read CC_TRIGGERS_CONFIG.yaml
        if not os.path.exists(CONFIG_FILE):
            print(f"Error: {CONFIG_FILE} not found")
            return
        
        with open(CONFIG_FILE, 'r') as file:
            config_lines = file.readlines()
        
        # Find and update NOW_AMOUNT line
        found = False
        for i, line in enumerate(config_lines):
            if line.strip().startswith(NOW_AMOUNT_KEY + ":"):
                current_value = float(line.split(":")[1].strip())
                new_value = round(current_value + start_amount, DECIMAL_PLACES)
                config_lines[i] = f"{NOW_AMOUNT_KEY}: {new_value}\n"
                found = True
                break
        
        if not found:
            print(f"Error: {NOW_AMOUNT_KEY} not found in {CONFIG_FILE}")
            return
        
        # Write back to CC_TRIGGERS_CONFIG.yaml
        with open(CONFIG_FILE, 'w') as file:
            file.writelines(config_lines)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()