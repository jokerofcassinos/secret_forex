import os
import sys
import numpy as np
import pandas as pd

# Configuração de Caminhos
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
    
    bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")
    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)

if root_path not in sys.path:
    sys.path.insert(0, root_path)
    
bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")
if bin_path not in sys.path:
    sys.path.insert(0, bin_path)

try:
    import qgc_engine
except ImportError as e:
    print(f"FAIL: qgc_engine não encontrado. Erro: {e}")

class QuantumGlassNode:
    """
    Orquestrador ASI-5 do Quantum Liquidity Glass.
    Usa limiares de Z-Score dinâmicos e passa ATR para evaporação (Radiação Hawking Relativística).
    """
    def __init__(self):
        self.engine = qgc_engine.QGCEngine()
        
    def scan_for_condensates(self, df):
        if len(df) < 50: return
        
        # Filtra picos de volume via Z-Score Dinâmico em janelas
        vols = df['tick_volume'].values
        v_mean = pd.Series(vols).rolling(20, min_periods=1).mean().values
        v_std = pd.Series(vols).rolling(20, min_periods=1).std().replace(0, 1e-9).fillna(1e-9).values
        z_scores = (vols - v_mean) / v_std
        
        # ATR Dinâmico para Decaimento de Hawking
        atr_series = (df['high'] - df['low']).rolling(14, min_periods=1).mean().fillna(10.0).values
        
        # SCANNER HISTÓRICO: Na primeira execução ou em picos novos, popula o engine
        active_count = len(self.engine.get_active_zones())
        if active_count == 0:
            print(f"[QGC-Node] Iniciando Scanner de Memória Histórica ASI-5...")
            lookback = min(800, len(df))
            for i in range(len(df) - lookback, len(df)):
                if z_scores[i] > 2.0: # Threshold Dinâmico Anti-Ruído
                    self.engine.add_zone(df['close'].iloc[i], z_scores[i], float(i))
                # Aplica a radiação de Hawking durante a passagem do tempo histórico
                self.engine.update_evaporation(float(i), df['close'].iloc[i], atr_series[i])
        
        # Detecção de novos picos em tempo real
        last_idx = len(df) - 1
        if z_scores[-1] > 2.0:
            self.engine.add_zone(df['close'].iloc[-1], z_scores[-1], float(last_idx))
            
        # Motor Termodinâmico Atualizado (Recebe ATR)
        self.engine.update_evaporation(float(last_idx), df['close'].iloc[-1], atr_series[-1])
        
    def get_gravity_telemetry(self, current_price, current_idx):
        pull = self.engine.calculate_gravity_pull(current_price)
        zones = self.engine.get_active_zones()
        for z in zones:
             z['age'] = current_idx - z['age'] # Convert to relative bars
        return {
            "gravity_pull": pull,
            "active_zones": zones,
            "zone_count": len(zones)
        }
