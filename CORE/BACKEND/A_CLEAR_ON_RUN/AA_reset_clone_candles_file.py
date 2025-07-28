import yaml
import os

# Configuration settings
FILE_PATHS = [
    "CORE/DATA/E_small_old_candles_data.yaml",
    "CORE/DATA/F_large_old_candles_data.yaml"
]

def load_yaml_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def save_yaml_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.safe_dump(data, file, allow_unicode=True)

def set_non_null_to_null(data):
    if isinstance(data, dict):
        return {key: set_non_null_to_null(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [set_non_null_to_null(item) for item in data]
    elif data is not None:
        return None
    return data

def main():
    for file_path in FILE_PATHS:
        try:
            # Load YAML file
            data = load_yaml_file(file_path)
            
            # Process data to set non-null values to null
            modified_data = set_non_null_to_null(data)
            

            # Save modified data back to file
            save_yaml_file(file_path, modified_data)
            

        except FileNotFoundError as e:
            raise e
        except Exception as e:
            raise Exception(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    main()

# print(f"- - A - - Old files nulled")
