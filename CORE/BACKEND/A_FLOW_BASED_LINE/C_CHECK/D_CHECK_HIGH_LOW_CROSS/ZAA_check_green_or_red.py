import yaml
import subprocess
import os

# Define script lists
SCRIPTS_GREEN = [
    "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FAAA_check_inside_outside_green_cross.py",
]

SCRIPTS_RED = [
    "CORE/BACKEND/F_CHECK_HIGH_LOW_CROSS/FAAB_check_inside_outside_red_cross.py",
]

def read_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None

def execute_scripts(script_list):
    for script in script_list:
        try:
            if os.path.exists(script):
                subprocess.run(["python", script], check=True)
            else:
                print(f"Script not found: {script}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing script {script}: {e}")
        except Exception as e:
            print(f"Unexpected error executing script {script}: {e}")

def main():
    config_file = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"
    
    # Read the YAML configuration
    config = read_yaml_file(config_file)
    
    if config is None:
        print("Failed to read configuration. Exiting.")
        return
    
    # Get PERCENT_STATUS value
    percent_status = config.get('PERCENT_STATUS')
    
    if percent_status is None:
        print("PERCENT_STATUS not found in configuration. Exiting.")
        return
    
    # Check if PERCENT_STATUS is positive or negative
    try:
        percent_value = float(percent_status)
        if percent_value > 0:
            execute_scripts(SCRIPTS_GREEN)
        elif percent_value < 0:
            execute_scripts(SCRIPTS_RED)
        else:
            print("PERCENT_STATUS is zero. No scripts will be executed.")
    except ValueError:
        print(f"Invalid PERCENT_STATUS value: {percent_status}. Must be a number.")

if __name__ == "__main__":
    main()