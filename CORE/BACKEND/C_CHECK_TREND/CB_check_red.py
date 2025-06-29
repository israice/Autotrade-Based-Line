import sys
import os
sys.dont_write_bytecode = True

scripts = [
    'CBA_run1.py',
    'CBB_run2.py',
]

for script in scripts:
    script_path = os.path.join(os.path.dirname(__file__), script)
    try:
        with open(script_path, encoding='utf-8') as f:
            code = compile(f.read(), script_path, 'exec')
            exec(code, {'__name__': '__main__'})
    except Exception as e:
        print(f'Error while running {script}: {e}')
        break
