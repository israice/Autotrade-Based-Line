import sys
import os
import shutil
sys.dont_write_bytecode = True

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
shutil.copyfile(
    os.path.join(project_root, 'CORE/DATA/A_fetch_candles.yaml'),
    os.path.join(project_root, 'CORE/DATA/Z_clone_candles.yaml'),
)
