import yaml
import subprocess

# Configuration
YAML_FILE_PATH = "CORE/DATA/CC_TRIGGERS_CONFIG.yaml"
the_key = "CROSSING_UP_GREEN"
CROSSING_UP_GREEN = "WATING"
SCRIPTS = [
    "CORE/TOOLS/msg_crossing_up_green.py", 
    "CORE/TOOLS/ADD_1_to_COUNTER_HIGH_CROSSING.py",
    "CORE/TOOLS/DISABLE_CROSSING_UP_GREEN.py",
    "CORE/TOOLS/ENABLE_CROSSING_DOWN_GREEN.py",
    "CORE/TOOLS/DISABLE_CROSSING_UP_RED.py",
    "CORE/TOOLS/DISABLE_CROSSING_DOWN_RED.py",
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