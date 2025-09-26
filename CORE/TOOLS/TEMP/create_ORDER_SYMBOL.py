import re
import os

# Configuration
# #####################
SOURCE_FILE = "settings.yaml"
SOURCE_VARIABLE = "symbol"

TARGET_FILE = "CORE/DATA/DD_ORDER_BODY.yaml"
TARGET_VARIABLE = "ORDER_SYMBOL"
# #####################

# Logic
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def main():
    # Read source and target files
    source_content = read_file(SOURCE_FILE)
    target_content = read_file(TARGET_FILE)
    
    # Find source variable value
    source_match = re.search(rf'^{SOURCE_VARIABLE}\s*:\s*([^\n]*)', source_content, re.MULTILINE)
    if not source_match:
        print(f"Variable {SOURCE_VARIABLE} not found in {SOURCE_FILE}")
        return
    
    source_value = source_match.group(1).strip()
    
    # Check if target needs updating
    target_match = re.search(rf'^{TARGET_VARIABLE}\s*:\s*([^\n]*)', target_content, re.MULTILINE)
    if target_match and target_match.group(1).strip() == source_value:
        return
    
    # Replace target variable value while preserving comments and formatting
    if target_match:
        updated_content = re.sub(
            rf'^{TARGET_VARIABLE}\s*:\s*[^\n]*',
            f'{TARGET_VARIABLE}: {source_value}',
            target_content,
            count=1,
            flags=re.MULTILINE
        )
        write_file(TARGET_FILE, updated_content)
    else:
        print(f"Variable {TARGET_VARIABLE} not found in {TARGET_FILE}")

if __name__ == "__main__":
    main()