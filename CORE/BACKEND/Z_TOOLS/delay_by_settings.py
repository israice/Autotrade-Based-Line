import yaml
import time

with open('CORE/DATA/user_settings.yaml', 'r') as file:
    delay_by_settings = yaml.safe_load(file)['delay_by_settings']

time.sleep(delay_by_settings)