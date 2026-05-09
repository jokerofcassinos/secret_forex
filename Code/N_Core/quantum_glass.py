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
        
        # Filtra picos de volume via Z-Score (Mais sensível: 1.5 sigma)
        vols = df['tick_volume'].values
        v_mean = np.mean(vols)
        v_std = np.std(vols) + 1e-9
        z_scores = (vols - v_mean) / v_std
        
        # SCANNER HISTÓRICO: Na primeira execução ou em picos novos, popula o engine
        # Verificamos se o engine está vazio para forçar o preenchimento histórico
        active_count = len(self.engine.get_active_zones())
        if active_count == 0:
            print(f"[QGC-Node] Iniciando Scanner de Memória Histórica (Threshold: 1.5 sigma)...")
            lookback = min(200, len(df))
            for i in range(len(df) - lookback, len(df)):
                if z_scores[i] > 1.5:
                    self.engine.add_zone(df['close'].iloc[i], z_scores[i], float(i))
        
        # Detecção de novos picos em tempo real
        last_idx = len(df) - 1
        if z_scores[-1] > 1.5:
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
