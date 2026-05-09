"""
Fast Build script for MSNR Engine using MinGW g++.
Compiles the Spectral Alchemist into a .pyd module.
"""
import os
import subprocess
import sys
import sysconfig
import pybind11
import shutil

# Paths
GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"

# Metadata
NAME = "msnr_engine"
SRC = "src/msnr/msnr_engine.cpp"
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'
OUTPUT = f"{NAME}{EXT_SUFFIX}"

def build():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    cmd = [
        GCC, "-shared", "-O3", "-ffast-math", "-std=c++17", "-D_USE_MATH_DEFINES",
        "-DNDEBUG", "-DMS_WIN64", "-fopenmp",
        f"-I{PYBIND_INC}", f"-I{PY_INC}", f"-L{PY_LIBS}",
        "-lpython313", "-o", OUTPUT, SRC,
    ]
    
    print(f"\n[FAST-BUILD] Compilando {NAME}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"  [OK] Sucesso: {OUTPUT}")
        # Deploy
        root_deploy = os.path.join("..", "..", OUTPUT)
        bin_deploy = os.path.join("bin", OUTPUT)
        
        if not os.path.exists("bin"): os.makedirs("bin")
        shutil.copy2(OUTPUT, bin_deploy)
        shutil.copy2(OUTPUT, root_deploy)
        print(f"  [DEPLOY] Implantado na raiz e em bin/.")
    else:
        print(f"  [FAIL] Erro na compilação:")
        print(result.stderr)

if __name__ == "__main__":
    build()
