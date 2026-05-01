import os
import sys

sys.path.append(os.path.abspath('Code/CPP_Engine/bin'))
sys.path.append(os.path.abspath('Code/CPP_Engine'))

if os.name == 'nt':
    mingw_bin = r"D:\msys64\mingw64\bin"
    if os.path.exists(mingw_bin):
        os.add_dll_directory(mingw_bin)

import qrw_engine

engine = qrw_engine.QRWEngine(201)

deltas = [10.0] * 20
volumes = [5000.0] * 20
skew = engine.compute_interference_skew(deltas, volumes)
print(f"Skew with purely positive deltas: {skew}")

deltas = [-10.0] * 20
skew = engine.compute_interference_skew(deltas, volumes)
print(f"Skew with purely negative deltas: {skew}")

deltas = [0.0] * 20
skew = engine.compute_interference_skew(deltas, volumes)
print(f"Skew with zero deltas (perfectly symmetric): {skew}")
