import sys
import os
sys.path.append(os.getcwd())
import qrw_engine
try:
    print("Testing (steps=2000, particles=1000)...")
    engine = qrw_engine.QRWEngine(2000, 1000)
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Testing (positions=401)...")
    engine = qrw_engine.QRWEngine(401)
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
