import os
import subprocess
import sys
import sysconfig
import pybind11

GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'

def build_engine(name, src):
    output = f"{name}{EXT_SUFFIX}"
    cmd = [
        GCC, "-shared", "-O3", "-ffast-math", "-std=c++17", "-fopenmp",
        "-D_USE_MATH_DEFINES", "-DNDEBUG", "-DMS_WIN64",
        f"-I{PYBIND_INC}", f"-I{PY_INC}", f"-L{PY_LIBS}",
        "-lpython313", "-o", output, src,
    ]
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[OK] {name}")
        return True
    else:
        print(f"[FAIL] {name}\n{result.stderr}")
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_engine("schrodinger_engine", "src/schrodinger/schrodinger_engine.cpp")
