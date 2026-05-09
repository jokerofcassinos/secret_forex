import os
import sys
import traceback

print("Checking DLL directories...")
mingw = r"D:\msys64\mingw64\bin"
if os.path.exists(mingw):
    print(f"Adding {mingw}")
    os.add_dll_directory(mingw)
    
root = os.getcwd()
print(f"Adding root: {root}")
os.add_dll_directory(root)
sys.path.insert(0, root)

try:
    print("Attempting to import qdd_engine...")
    import qdd_engine
    print("SUCCESS: qdd_engine imported.")
    print(f"File: {qdd_engine.__file__}")
except Exception as e:
    print("FAILED: qdd_engine import raised exception:")
    traceback.print_exc()
except SystemExit as e:
    print(f"FAILED: qdd_engine import caused SystemExit: {e}")
except BaseException as e:
    print(f"FAILED: qdd_engine import caused hard crash/BaseException: {type(e)}")
    traceback.print_exc()

print("End of script.")
