import ruamel.yaml
import os

# Configuration settings
CONFIG_FILE = "CORE/DATA/triggers_config.yaml"
SCRIPTS = [
    "TOOLS/message_long_sell_percent_market_order.py"
]
PERCENT_STATUS_KEY = "PERCENT_STATUS"
PERCENT_LONG_SELL_KEY = "PERCENT_LONG_SELL"
SETTINGS_PERCENT_SELL_KEY = "SETTINGS_PERCENT_SELL"

def load_config():
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(CONFIG_FILE, 'r') as file:
        return yaml.load(file)

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
    percent_status = config[PERCENT_STATUS_KEY]
    percent_long_sell = config[PERCENT_LONG_SELL_KEY]
    settings_percent_sell = config[SETTINGS_PERCENT_SELL_KEY]
    
    # Check if PERCENT_STATUS > PERCENT_LONG_SELL
    if percent_status > percent_long_sell:
        # Calculate how much to add to PERCENT_LONG_SELL to exceed PERCENT_STATUS
        difference = percent_status - percent_long_sell
        additional_percent = settings_percent_sell
        
        # Keep adding SETTINGS_PERCENT_SELL until PERCENT_LONG_SELL exceeds PERCENT_STATUS
        while percent_long_sell <= percent_status:
            percent_long_sell += additional_percent
        
        # Format PERCENT_LONG_SELL to X.XXX
        formatted_percent_long_sell = float(f"{percent_long_sell:.3f}")
        
        # Update configuration
        config[PERCENT_LONG_SELL_KEY] = formatted_percent_long_sell
        save_config(config)
        
        # Run scripts
        run_scripts()

if __name__ == "__main__":
    main()