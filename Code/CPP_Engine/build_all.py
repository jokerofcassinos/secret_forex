"""
Build script for all C++ engines using MinGW g++.
Compiles each engine into a .pyd extension module for Python 3.13.
"""
import os
import subprocess
import sys
import sysconfig
import pybind11

# Paths
GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"  # Link directly to python313.dll

# Python extension suffix
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'

# Engines to build
ENGINES = [
    ("mhd_engine",        "src/mhd/mhd_engine.cpp"),
    ("qrw_engine",        "src/qrw/qrw_engine.cpp"),
    ("schrodinger_engine", "src/schrodinger/schrodinger_engine.cpp"),
    ("rmt_engine",        "src/rmt/rmt_engine.cpp"),
    ("lbm_engine",        "src/lbm/lbm_engine.cpp"),
    ("qdd_engine",        "src/qdd/qdd_engine.cpp"),
    ("qho_engine",        "src/qho/qho_engine.cpp"),
    ("cyt_engine",        "src/cyt/cyt_engine.cpp"),
]

def build_engine(name, src):
    output = f"{name}{EXT_SUFFIX}"
    cmd = [
        GCC,
        "-shared",
        "-O3",
        "-ffast-math",
        "-std=c++17",
        "-D_USE_MATH_DEFINES",
        "-DNDEBUG",
        "-fopenmp",
        f"-I{PYBIND_INC}",
        f"-I{PY_INC}",
        f"-L{PY_LIBS}",
        "-lpython313",
        "-o", output,
        src,
    ]
    
    print(f"\n{'='*60}")
    print(f"[BUILD] {name}")
    print(f"  Source: {src}")
    print(f"  Output: {output}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        size = os.path.getsize(output) if os.path.exists(output) else 0
        print(f"  [OK] SUCCESS ({size:,} bytes)")
        return True
    else:
        print(f"  [FAIL] FAILED")
        if result.stdout: print(f"  stdout: {result.stdout}")
        if result.stderr: print(f"  stderr: {result.stderr}")
        return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Python: {sys.version}")
    print(f"Pybind11: {PYBIND_INC}")
    print(f"Compiler: {GCC}")
    print(f"Extension: {EXT_SUFFIX}")
    
    results = {}
    for name, src in ENGINES:
        results[name] = build_engine(name, src)
    
    print(f"\n{'='*60}")
    print("BUILD SUMMARY")
    print(f"{'='*60}")
    for name, ok in results.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {name}: {status}")
    
    total = sum(results.values())
    print(f"\n{total}/{len(ENGINES)} engines compiled successfully.")
