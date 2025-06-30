import sys
import os
import yaml
import subprocess
sys.dont_write_bytecode = True

# Получаем путь к корню проекта (три уровня вверх от текущего файла)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
yaml_path = os.path.join(project_root, 'CORE/DATA/A_fetch_candles.yaml')
with open(yaml_path, encoding='utf-8') as f:
    data = yaml.safe_load(f)

# data[0] - текущая свеча, data[1] - предыдущая свеча
candle_0_open = float(data[0]['candle_0_open'])
candle_1_open = float(data[1]['candle_1_open'])

# LONG
if candle_0_open > candle_1_open:
    scripts = [
        'CORE/BACKEND/C_CHECK_CANDLE_END/CAA_SELL_LONG.py', 
        ]
# SHORT
elif candle_0_open < candle_1_open:
    scripts = [
        'CORE/BACKEND/C_CHECK_CANDLE_END/CAB_SELL_SHORT.py', 
        ]
# СВЕЧА ЗАКРЫЛАСЬ ТАК ЖЕ КАК ПРЕДЫДУЩАЯ
else:
    scripts = [
        'CORE/BACKEND/C_CHECK_CANDLE_END/CAA_SELL_LONG.py', 
        'CORE/BACKEND/C_CHECK_CANDLE_END/CAB_SELL_SHORT.py', 
        ]

# Получаем путь к корню проекта (три уровня вверх от текущего файла)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

for script in scripts:
    script_path = os.path.join(project_root, script)
    try:
        # subprocess.run гарантирует отдельный процесс и правильную обработку ошибок
        subprocess.run([sys.executable, script_path], check=True)
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break
