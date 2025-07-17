import sys
import os
sys.dont_write_bytecode = True

# ==== НАСТРОЙКИ ====
PROJECT_ROOT_LEVELS_UP = 4
SCRIPTS = [
    'CORE/BACKEND/B_GET_DATA/A_large/AA_get_large_candles.py',
]
SCRIPT_ENCODING = 'utf-8'

# ==== ОСНОВНОЙ КОД ====
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * PROJECT_ROOT_LEVELS_UP)))
for script in SCRIPTS:
    script_path = os.path.join(project_root, script)
    try:
        with open(script_path, encoding=SCRIPT_ENCODING) as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': script_path})
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break

