import shutil
import os

# Define source and destination paths
file_pairs = [
    ("CORE/DATA/A_small_new_candles_data.yaml", "CORE/DATA/E_small_old_candles_data.yaml"),
    ("CORE/DATA/B_large_new_candles_data.yaml", "CORE/DATA/F_large_old_candles_data.yaml"),
    ("CORE/DATA/C_temp_config.yaml", "CORE/DATA/D_temp_old_config.yaml")
]

# Copy each file to its destination
for src, dst in file_pairs:
    try:
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # Copy file
        shutil.copy2(src, dst)
    except FileNotFoundError:
        print(f"Error: Source file {src} not found")
    except Exception as e:
        print(f"Error copying {src} to {dst}: {str(e)}")