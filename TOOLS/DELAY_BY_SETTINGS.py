import yaml
import time

with open('CORE/DATA/user_settings.yaml', 'r') as file:
    DELAY_BY_SETTINGS = yaml.safe_load(file)['DELAY_BY_SETTINGS']

time.sleep(DELAY_BY_SETTINGS)