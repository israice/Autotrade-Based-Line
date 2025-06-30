

import sys
import os
sys.dont_write_bytecode = True

scripts = [
    'CORE/BACKEND/C_CHECK_CANDLE_END/CAAA_sell_long_order.py',
    'CORE/BACKEND/C_CHECK_CANDLE_END/CAAB_reset_CANDLE_PERCENT_NOW.py',
]

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
for script in scripts:
    script_path = os.path.join(project_root, script)
    try:
        with open(script_path, encoding='utf-8') as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': script_path})
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break
