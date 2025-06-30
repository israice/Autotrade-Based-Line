import sys
import os
sys.dont_write_bytecode = True

scripts = [
    'CAA_finished_as_long.py',
    'CAB_price_now_bigger_then_high.py',
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
