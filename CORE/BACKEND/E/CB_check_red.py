import sys
import os
sys.dont_write_bytecode = True

scripts = [
    'CBA_finished_as_short.py',
    'CBB_price_now_lower_then_low.py',
]

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
for script in scripts:
    script_path = os.path.join(project_root, 'CORE/BACKEND/C_CHECK_TREND', script)
    try:
        with open(script_path, encoding='utf-8') as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': script_path})
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break
