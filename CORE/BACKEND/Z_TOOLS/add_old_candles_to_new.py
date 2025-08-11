import yaml

# Hardcoded new candle_0 data
new_candle_0 = {
    'candle_0_close_time': '2025-08-10 23:35:59',
    'candle_0_update_time': '2025-08-10 20:33:47',
    'candle_0_open_time': '2025-08-10 23:33:00',
    'candle_0_close': '3.1806',
    'candle_0_high': '3.1806',
    'candle_0_open': '3.1788',
    'candle_0_low': '3.1776'
}

# Paths
z_file_path = 'CORE\\DATA\\Z_candle.yaml'
a_file_path = 'CORE\\DATA\\A_candle.yaml'

# Read Z_candle.yaml
with open(z_file_path, 'r') as z_file:
    z_data = yaml.safe_load(z_file)

# Prepare new data list starting with new_candle_0
new_data = [new_candle_0]

# Shift the indices in Z data
for candle_dict in z_data:
    # Extract old number from the first key (assuming consistent)
    first_key = next(iter(candle_dict))
    old_num = int(first_key.split('_')[1])
    new_num = old_num + 1
    
    # Create new dict with shifted keys
    new_candle_dict = {}
    for key, value in candle_dict.items():
        new_key = key.replace(f'_{old_num}_', f'_{new_num}_')
        new_candle_dict[new_key] = value
    
    new_data.append(new_candle_dict)

# Write to A_candle.yaml
with open(a_file_path, 'w') as a_file:
    yaml.dump(new_data, a_file, default_flow_style=False, sort_keys=False, allow_unicode=True)