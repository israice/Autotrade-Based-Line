import shutil
import os

# Define source and destination paths
file_pairs = [
    ("CORE/DATA/A_candle.yaml", "CORE/DATA/Z_candle.yaml"),
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