import yaml
import subprocess

# Configuration settings and variables
CONFIG_FILE = 'CORE/DATA/CC_TRIGGERS_CONFIG.yaml'
GREEN_STATUS = 'GREEN'
RED_STATUS = 'RED'
PERCENT_STATUS_KEY = 'PERCENT_STATUS'
TREND_STATUS_KEY = 'TREND_STATUS'

GREEN_LIST = [
    "CORE/TOOLS/msg/up.py",
    "CORE/TOOLS/CC_triggers_config/add_1_to_COUNTER_OPEN_CROSSING.py",
]
RED_LIST = [
    "CORE/TOOLS/msg/down.py",
    "CORE/TOOLS/CC_triggers_config/add_1_to_COUNTER_OPEN_CROSSING.py",
]

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file) or {}

def save_config(file_path, new_trend_status):
    # Read the original file to preserve comments and structure
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Update only the TREND_STATUS line
    trend_status_found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{TREND_STATUS_KEY}:'):
            lines[i] = f"{TREND_STATUS_KEY}: {new_trend_status}\n"
            trend_status_found = True
            break
    
    # If TREND_STATUS is not found, append it
    if not trend_status_found:
        lines.append(f"{TREND_STATUS_KEY}: {new_trend_status}\n")
    
    # Write back to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)

def run_scripts(script_list):
    for script in script_list:
        subprocess.run(['python', script])

def main():
    config = load_config(CONFIG_FILE)
    percent_status = config.get(PERCENT_STATUS_KEY, 0)
    current_trend_status = config.get(TREND_STATUS_KEY, '')
    
    # Определяем валидные статусы
    valid_statuses = [GREEN_STATUS, RED_STATUS]
    
    # Определяем новый статус на основе percent_status
    if percent_status > 0:
        new_trend_status = GREEN_STATUS
        script_list = GREEN_LIST
    elif percent_status < 0:
        new_trend_status = RED_STATUS
        script_list = RED_LIST
    else:
        # Если percent_status == 0, не меняем статус
        return
    
    # Проверяем, нужно ли изменить статус
    if current_trend_status != new_trend_status:
        # Сохраняем новый статус
        save_config(CONFIG_FILE, new_trend_status)
        
        # Запускаем скрипты только если предыдущий статус был валидным
        # (т.е. не запускаем при первичной установке статуса)
        if current_trend_status in valid_statuses:
            run_scripts(script_list)

if __name__ == "__main__":
    main()
