

import sys
import os
sys.dont_write_bytecode = True

scripts = [
    'CORE/BACKEND/D_CHECK_SELL_PERCENT/DBA_sell_short_order.py',
    'CORE/BACKEND/D_CHECK_SELL_PERCENT/DBB_add_CANDLE_PERCENT_NEXT.py',
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
