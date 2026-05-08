import sys
import os
import numpy as np

if os.path.exists(r"D:\msys64\mingw64\bin"):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

try:
    import qrw_engine
    print("SUCCESS: QRW Engine Imported.")
    
    engine = qrw_engine.QRWEngine(401)
    print("SUCCESS: Instance Created.")
    
    engine.reset()
    print("SUCCESS: .reset() method exists.")
    
    d = np.array([10.0], dtype=float)
    v = np.array([100.0], dtype=float)
    scale = 0.01
    
    skew = 0
    var = 0
    for _ in range(100):
        skew = engine.update_and_get_skew(d, v, scale)
        var = engine.get_wave_variance()
        
    print(f"INFO: Simulation 100 bars done. Skew: {skew:.4f}, Var: {var:.4f}")
    
    if skew > 0.5:
        print("SUCCESS: Engine reacting to bias.")
    else:
        print("ERROR: Engine NOT reacting to bias.")

except Exception as e:
    print(f"ERROR: Diagnostic FAILED: {e}")
