import yaml
import subprocess

# Configuration
YAML_FILE_PATH = "CORE/DATA/triggers_config.yaml"
the_key = "CROSSING_UP_RED"
CROSSING_UP_GREEN = "WATING"
SCRIPTS = [
    "CORE/BACKEND/Z_TOOLS/message_CROSSING_UP_RED.py",
    "CORE/BACKEND/Z_TOOLS/add_1_to_COUNTER_LOW_CROSSING.py",
    "CORE/BACKEND/Z_TOOLS/enable_CROSSING_UP_GREEN.py",
    "CORE/BACKEND/Z_TOOLS/disable_CROSSING_DOWN_GREEN.py",
    "CORE/BACKEND/Z_TOOLS/disable_CROSSING_UP_RED.py",
    "CORE/BACKEND/Z_TOOLS/enable_CROSSING_DOWN_RED.py",
]

def load_yaml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None

def run_scripts(scripts):
    for script in scripts:
        try:
            subprocess.run(['python', script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")

def main():
    data = load_yaml_file(YAML_FILE_PATH)
    if data and data.get(the_key) == CROSSING_UP_GREEN:
        run_scripts(SCRIPTS)
        
if __name__ == "__main__":
    main()