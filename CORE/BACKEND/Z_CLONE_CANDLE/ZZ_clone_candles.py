import shutil
import sys
import os

# Список пар (откуда, куда)
file_pairs = [
    (
        "CORE/DATA/A_small_new_candles_data.yaml", 
        "CORE/DATA/D_small_old_candles_data.yaml"
    ),
    (
        "CORE/DATA/B_large_new_candles_data.yaml", 
        "CORE/DATA/E_large_old_candles_data.yaml"
    ),
]

for src, dst in file_pairs:
    if not os.path.isfile(src):
        print(f"Ошибка: файл {src} не найден!")
        sys.exit(1)
    try:
        shutil.copyfile(src, dst)
    except Exception as e:
        print(f"Ошибка при копировании {src} -> {dst}: {e}")
        sys.exit(1)

# print("- - Z - - Candles cloned successfully.")
