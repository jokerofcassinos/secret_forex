import os
import sys

# DEBUG QDD IMPORT
root = os.getcwd()
print(f"Current Dir: {root}")
print(f"Files: {os.listdir(root)}")

if sys.platform == 'win32':
    os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root)

sys.path.append(root)

try:
    import qdd_engine
    print("SUCCESS: qdd_engine imported!")
    print(f"Methods: {dir(qdd_engine.QDDEngine)}")
except Exception as e:
    print(f"FAILURE: {e}")
