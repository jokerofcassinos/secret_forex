import os
import sys
import numpy as np
import pandas as pd

print("DEBUG: Step 1 - Imports OK")

# Paths
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"DEBUG: Step 2 - Root path: {root}")

if sys.platform == 'win32':
    os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root)
sys.path.append(root)

print("DEBUG: Step 3 - DLLs and Path added")

try:
    import tensor_network
    print("DEBUG: Step 4 - tensor_network module imported")
    node = tensor_network.TensorNetworkNode()
    print("DEBUG: Step 5 - Node initialized")
except Exception as e:
    print(f"DEBUG: ERROR at Step 4/5: {e}")
    sys.exit(1)

# Generate simple data
n = 200
data = {
    'M1': pd.DataFrame({'close': np.random.normal(100, 1, n)}),
    'M5': pd.DataFrame({'close': np.random.normal(100, 1, n)})
}

print("DEBUG: Step 6 - Data generated")

try:
    f = node.calculate_global_alignment(data)
    print(f"DEBUG: Step 7 - Fidelity calculated: {f}")
except Exception as e:
    print(f"DEBUG: ERROR at Step 7: {e}")
    sys.exit(1)

print("DEBUG: SUCCESS - Minimal test passed")
