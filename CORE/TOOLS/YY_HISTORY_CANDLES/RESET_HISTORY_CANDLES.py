file_path = 'CORE/DATA/YY_HISTORY_CANDLES.yaml'

with open(file_path, 'r+') as f:
    header = f.readline()
    f.seek(0)
    f.write(header)
    f.truncate()