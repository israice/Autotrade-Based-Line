file_path = 'CORE/DATA/Y_database.csv'

with open(file_path, 'r+') as f:
    header = f.readline()
    f.seek(0)
    f.write(header)
    f.truncate()