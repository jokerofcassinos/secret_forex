import os
import subprocess
import sys
import sysconfig
import pybind11
import shutil

# NEXUS QDD FAST BUILDER (STANDARD COMPLIANT)
GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'

target_name = "qdd_engine"
src = "src/qdd/qdd_engine.cpp"
output = f"{target_name}{EXT_SUFFIX}"

print(f"[NEXUS] Iniciando build padrao para: {target_name}")

cmd = [
    GCC, "-shared", "-O3", "-ffast-math", "-std=c++17", "-D_USE_MATH_DEFINES",
    "-DNDEBUG", "-DMS_WIN64", "-fopenmp",
    f"-I{PYBIND_INC}", f"-I{PY_INC}", f"-L{PY_LIBS}",
    "-lpython313", "-o", output, src,
]

try:
    print(f"Comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("SUCCESS: QDD Engine compilado.")
        # Deploy
        bin_path = os.path.join("bin", output)
        root_deploy_path = os.path.join("..", "..", output)
        
        if not os.path.exists("bin"): os.makedirs("bin")
        shutil.copy2(output, bin_path)
        shutil.copy2(output, root_deploy_path)
        print(f"Deploy realizado para: {root_deploy_path}")
    else:
        print("FAILED")
        print(result.stderr)
except Exception as e:
    print(f" ERROR: {e}")
