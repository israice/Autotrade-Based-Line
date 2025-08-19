# =========================
# Settings
# =========================
FILE_PATHS = [
    'CORE/DATA/AA_CANDLE.yaml',
    'CORE/DATA/ZZ_CANDLE.yaml',
]

# =========================
# Logic
# =========================
for file_path in FILE_PATHS:
    # Open each file for read/write without recreating it
    # Goal: keep only the first line (header) and truncate the rest
    with open(file_path, 'r+', encoding='utf-8') as f:
        header = f.readline()      # Read the first line
        f.seek(0)                  # Rewind to the beginning
        f.write(header)            # Write back only the header
        f.truncate()               # Remove the remainder of the file
