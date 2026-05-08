import os
import subprocess
import sys
import sysconfig
import pybind11
import shutil

GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'

ROOT_DIR = r"d:\AI Brain\US30"
CPP_DIR = os.path.join(ROOT_DIR, "Code", "CPP_Engine")

def build_qrw():
    os.chdir(CPP_DIR)
    name = "qrw_engine"
    src = "src/qrw/qrw_engine.cpp"
    output = f"{name}{EXT_SUFFIX}"
    
    cmd = [
        GCC, "-shared", "-O3", "-ffast-math", "-std=c++17",
        "-D_USE_MATH_DEFINES", "-DNDEBUG",
        f"-I{PYBIND_INC}", f"-I{PY_INC}", f"-L{PY_LIBS}",
        "-lpython313", "-o", output, src,
    ]
    
    print(f"BUILDING QRW (4001 Grid Resolution)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: QRW COMPILED.")
        dst = os.path.join(ROOT_DIR, output)
        shutil.copy2(output, dst)
        print(f"INFO: BINARY DEPLOYED TO ROOT: {dst}")
        shutil.copy2(output, os.path.join(ROOT_DIR, f"{name}.pyd"))
        return True
    else:
        print(f"ERROR: COMPILATION FAILED:\n{result.stderr}")
        return False

if __name__ == "__main__":
    build_qrw()
