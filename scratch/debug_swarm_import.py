import os
import sys
import traceback

print("Diagnostic: Starting Aethelgard_Swarm import debug...")
root = os.getcwd()
sys.path.insert(0, root)

if os.name == 'nt':
    mingw = r"D:\msys64\mingw64\bin"
    if os.path.exists(mingw):
        os.add_dll_directory(mingw)
    os.add_dll_directory(root)

try:
    print("Step 1: Importing base dependencies...")
    import numpy as np
    import pandas as pd
    import zmq
    import MetaTrader5 as mt5
    print("Base dependencies OK.")

    print("Step 2: Importing local modules...")
    
    print("  > quantum_indicators...")
    from Code.N_Core.quantum_indicators import QuantumIndicators
    print("  OK.")

    print("  > msnr_alchemist...")
    from Code.N_Core.msnr_alchemist import MSNRAlchemist
    print("  OK.")

    print("  > quantum_oracle...")
    from Code.N_Core.quantum_oracle import QuantumOracle
    print("  OK.")

    print("  > yield_governor...")
    from Code.N_Core.yield_governor import YieldGovernor
    print("  OK.")

    print("  > mt5_bridge...")
    from Code.R_Exec.mt5_bridge import MT5NeuralBridge
    print("  OK.")

    print("Step 3: Importing Aethelgard_Swarm...")
    import Aethelgard_Swarm
    print("SUCCESS: Aethelgard_Swarm imported.")

except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
except SystemExit as e:
    print(f"SystemExit: {e}")
except BaseException as e:
    print(f"Hard crash of type: {type(e)}")
    traceback.print_exc()

print("End of diagnostic.")
