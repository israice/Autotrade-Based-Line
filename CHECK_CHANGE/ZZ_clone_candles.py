import sys
sys.dont_write_bytecode = True
import shutil
shutil.copyfile('CHECK_CHANGE/AA_fetch_candles.yaml', 'CHECK_CHANGE/ZZ_clone_candles.yaml')
