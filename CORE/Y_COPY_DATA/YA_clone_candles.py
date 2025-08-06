import shutil
import os

# Define source and destination paths
file_pairs = [
    ("CORE/B_GET_DATA/BA_get_large_candle.yaml", "CORE/Y_COPY_DATA/YA_clone_candles.yaml"),
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