import sys
import os
# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())
try:
    import qrw_engine
    print(f"Module found: {qrw_engine}")
    print(f"Attributes: {dir(qrw_engine)}")
except Exception as e:
    print(f"Error: {e}")
