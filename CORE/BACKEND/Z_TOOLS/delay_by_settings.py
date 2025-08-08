import yaml
import time

with open('CORE/DATA/settings.yaml', 'r') as file:
    delay = yaml.safe_load(file)['delay']

time.sleep(delay)