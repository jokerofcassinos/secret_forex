import sys
import os

# Add bin path
root = os.path.abspath(os.getcwd())
bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
sys.path.insert(0, bin_path)
if os.name == 'nt':
    os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(bin_path)

try:
    import qrw_engine
    print("SUCCESS: qrw_engine loaded")
    engine = qrw_engine.QRWEngine(401)
    print("SUCCESS: QRWEngine instantiated")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
