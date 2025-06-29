import sys
import shutil
sys.dont_write_bytecode = True

shutil.copyfile(
    'CORE/DATA/A_fetch_candles.yaml', 
    'CORE/DATA/Z_clone_candles.yaml',
    )
