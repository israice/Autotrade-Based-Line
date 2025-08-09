import ruamel.yaml
import os

# Configuration settings
CONFIG_FILE = "CORE/DATA/triggers_config.yaml"
SCRIPTS = [
    "CORE/BACKEND/Z_TOOLS/message_short_sell_percent_market_order.py"
]
PERCENT_STATUS_KEY = "PERCENT_STATUS"
PERCENT_SHORT_SELL_KEY = "PERCENT_SHORT_SELL"
SETTINGS_PERCENT_SELL_KEY = "SETTINGS_PERCENT_SELL"

def load_config():
    try:
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.indent(mapping=2, sequence=4, offset=2)
        with open(CONFIG_FILE, 'r') as file:
            config = yaml.load(file)
        # Validate required keys
        for key in [PERCENT_STATUS_KEY, PERCENT_SHORT_SELL_KEY, SETTINGS_PERCENT_SELL_KEY]:
            if key not in config:
                raise KeyError(f"Missing key {key} in {CONFIG_FILE}")
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        raise

def save_config(config):
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config, file)

def run_scripts():
    for script in SCRIPTS:
        os.system(f"python {script}")


def main():
    # Load configuration
    config = load_config()
    
    # Get variables
    percent_status = float(config[PERCENT_STATUS_KEY])
    percent_short_sell = float(config[PERCENT_SHORT_SELL_KEY])
    settings_percent_sell = float(config[SETTINGS_PERCENT_SELL_KEY])
    
    # Validate SETTINGS_PERCENT_SELL is positive
    if settings_percent_sell <= 0:
        print(f"Error: {SETTINGS_PERCENT_SELL_KEY} must be positive, got {settings_percent_sell}")
        return
    
    # Check if PERCENT_SHORT_SELL > PERCENT_STATUS (i.e., less negative)
    if percent_short_sell > percent_status:
        # Calculate how much to subtract to make PERCENT_SHORT_SELL <= PERCENT_STATUS
        difference = percent_short_sell - percent_status
        decrement = settings_percent_sell
        
        # Keep subtracting SETTINGS_PERCENT_SELL until PERCENT_SHORT_SELL <= PERCENT_STATUS
        while percent_short_sell > percent_status:
            percent_short_sell -= decrement
        
        # Format PERCENT_SHORT_SELL to X.XXX, preserving sign
        formatted_percent_short_sell = round(percent_short_sell, 3)
        
        # Update configuration
        config[PERCENT_SHORT_SELL_KEY] = formatted_percent_short_sell
        save_config(config)
        
        # Run scripts
        run_scripts()

if __name__ == "__main__":
    main()
