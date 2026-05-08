import os
import sys

# Add MinGW bin to DLL path
mingw_bin = r"D:\msys64\mingw64\bin"
if os.path.exists(mingw_bin):
    os.add_dll_directory(mingw_bin)

# Add current dir to path
root = os.path.abspath(".")
sys.path.insert(0, root)
os.add_dll_directory(root)

try:
    import rht_engine
    print("rht_engine: LOAD SUCCESS")
    import qdd_engine
    print("qdd_engine: LOAD SUCCESS")
except Exception as e:
    print(f"LOAD FAILED: {e}")
