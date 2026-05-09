import os
import sys
import numpy as np
import pandas as pd

# Configuração de Caminhos
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

try:
    import qgc_engine
except ImportError:
    print("FAIL: qgc_engine não encontrado.")

class QuantumGlassNode:
    """
    Orquestrador Recalibrado do Quantum Liquidity Glass.
    Usa Z-Score para detecção e permite agregação de massa no C++.
    """
    def __init__(self):
        self.engine = qgc_engine.QGCEngine()
        
    def scan_for_condensates(self, df):
        if len(df) < 50: return
        
        # Filtra picos de volume via Z-Score (Muito mais robusto)
        vols = df['tick_volume'].values
        v_mean = np.mean(vols)
        v_std = np.std(vols) + 1e-9
        z_scores = (vols - v_mean) / v_std
        
        # Só pega o último se for um pico massivo (> 3 sigmas)
        last_idx = len(df) - 1
        if z_scores[-1] > 3.0:
            self.engine.add_zone(df['close'].iloc[-1], z_scores[-1], float(last_idx))
            
        self.engine.update_evaporation(float(last_idx), df['close'].iloc[-1])
        
    def get_gravity_telemetry(self, current_price):
        pull = self.engine.calculate_gravity_pull(current_price)
        zones = self.engine.get_active_zones()
        return {
            "gravity_pull": pull,
            "active_zones": zones,
            "zone_count": len(zones)
        }
