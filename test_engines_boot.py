
import sys
import os
import zmq
import numpy as np

if os.name == 'nt':
    root_path = os.path.dirname(__file__)
    if root_path not in sys.path: sys.path.insert(0, root_path)
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")

try:
    import cyt_engine
    cyt = cyt_engine.CYTEngine()
    print("✅ cyt_engine OK")
except Exception as e:
    print(f"❌ cyt_engine ERROR: {e}")

try:
    from Code.N_Core.quantum_clouds import QuantumCloudTracker
    print("✅ QuantumCloudTracker OK")
except Exception as e:
    print(f"❌ QuantumCloudTracker ERROR: {e}")

try:
    from Code.N_Core.fluid_dynamics import LBMFluidDynamics
    print("✅ LBMFluidDynamics OK")
except Exception as e:
    print(f"❌ LBMFluidDynamics ERROR: {e}")
