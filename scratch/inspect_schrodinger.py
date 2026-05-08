import os
import sys

project_root = r"d:\AI Brain\US30"
sys.path.append(os.path.join(project_root, 'Code', 'CPP_Engine'))
sys.path.append(os.path.join(project_root, 'Code', 'CPP_Engine', 'bin'))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
    import schrodinger_engine
    print(f"Module file: {schrodinger_engine.__file__}")
    print(f"Methods: {dir(schrodinger_engine.QuantumCloudSolver)}")
except Exception as e:
    print(f"Error: {e}")
