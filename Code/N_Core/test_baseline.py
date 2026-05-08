import os
import sys

print("DEBUG: Step 0 - Basic Imports OK")

try:
    import numpy as np
    print("DEBUG: Step 1 - Numpy OK")
except Exception as e:
    print(f"DEBUG: Numpy FAIL: {e}")

try:
    import pandas as pd
    print("DEBUG: Step 2 - Pandas OK")
except Exception as e:
    print(f"DEBUG: Pandas FAIL: {e}")

print("DEBUG: FINISHED")
