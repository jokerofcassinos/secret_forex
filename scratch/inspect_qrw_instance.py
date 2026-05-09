import sys
import os
sys.path.append(os.getcwd())
import qrw_engine
try:
    engine = qrw_engine.QRWEngine(401)
    print(f"Engine Instance: {engine}")
    print(f"Attributes: {dir(engine)}")
except Exception as e:
    print(f"Error: {e}")
