import yaml
import time

with open('settings.yaml') as file:
    # Загружаем данные из файла
    settings = yaml.safe_load(file)
    # Получаем значение и сразу преобразуем его в число (float)
    DELAY_BY_SETTINGS = float(settings['DELAY_BY_SETTINGS'])

time.sleep(DELAY_BY_SETTINGS)
