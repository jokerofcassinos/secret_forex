import os
import sys
import numpy as np
import pandas as pd

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++
if os.name == 'nt':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)
        if bin_path not in sys.path:
            sys.path.insert(0, bin_path)

try:
    import cyt_engine as cyt_engine_module
except ImportError as e:
    raise RuntimeError(f"FALHA CRÍTICA: Motor CYT (C++) não encontrado na raiz. {e}")


class YieldGovernor:
    """
    Agente Yield-Governor v5.0: Ricci Flow (ASI-5).
    Usa o verdadeiro Tensor de Ricci para curvar o lote (Shield) em caso de Buracos Negros de Liquidez.
    Implementa Histerese Topológica para evitar efeito estroboscópio.
    """
    def __init__(self, danger_window=20):
        self.engine = cyt_engine_module.CYTEngine()
        self.danger_window = danger_window
        self.shield_active = False
        self.shield_level = 0.0
        self.cooldown_counter = 0

    def monitor_topology(self, df_slice: pd.DataFrame, qrw_skew: float = 0.0):
        """
        Recebe as últimas barras, constrói a Matriz de 10 Dimensões (Features),
        avalia o Tensor de Ricci em tempo real e agora integra a Entropia Estocástica do QRW.
        """
        if len(df_slice) < self.danger_window:
            return {'deformation': 0.0, 'shield_active': False, 'shield_level': 0.0, 'is_collapsed': False}

        # 1. Feature Matrix Extraction (10D Tensor para Ricci)
        data_10d = np.zeros((10, len(df_slice)))
        data_10d[0, :] = df_slice['open'].values
        data_10d[1, :] = df_slice['high'].values
        data_10d[2, :] = df_slice['low'].values
        data_10d[3, :] = df_slice['close'].values
        data_10d[4, :] = df_slice.get('tick_volume', pd.Series(np.ones(len(df_slice)))).values
        data_10d[5, :] = df_slice['close'].pct_change().fillna(0).values
        data_10d[6, :] = (df_slice['high'] - df_slice['low']).values
        data_10d[7, :] = np.abs(df_slice['close'] - df_slice['open']).values
        data_10d[8, :] = (df_slice['high'] - np.maximum(df_slice['open'], df_slice['close'])).values
        data_10d[9, :] = (np.minimum(df_slice['open'], df_slice['close']) - df_slice['low']).values

        # 2. Física Riemanniana
        flow = self.engine.analyze_manifold_flow(data_10d)
        ricci_scalar = flow.get("deformation", np.zeros(len(df_slice)))
        
        if len(ricci_scalar) < self.danger_window:
            return {'deformation': 0.0, 'shield_active': False, 'shield_level': 0.0, 'is_collapsed': False}

        # Avalia a gravidade atual
        current_ricci = ricci_scalar[-1]
        
        # [v2.5] ENTROPIA ESTOCÁSTICA (QRW SKEWNESS)
        # Uma assimetria extrema (perto de 1.0 ou -1.0) ou bimodalidade causa instabilidade na onda.
        stochastic_entropy = abs(qrw_skew)
        
        # 3. HISTERESE TOPOLÓGICA (ASI-5)
        # Combinamos Ricci (Curvatura) com QRW (Assimetria)
        z_score_absoluto = abs(current_ricci) / (np.std(ricci_scalar[-self.danger_window:]) + 1e-9)
        
        # Se Z-Score > 2.5 ou Entropia Quântica > 0.8, Shield Ativa.
        if z_score_absoluto > 2.5 or stochastic_entropy > 0.8:
            # Shield level escala com o maior dos perigos
            self.shield_level = max(
                min(1.0, (z_score_absoluto - 2.5) / 2.0),
                min(1.0, (stochastic_entropy - 0.7) * 3.0)
            )
            self.shield_active = True
            self.cooldown_counter = 5 
        else:
            if self.cooldown_counter > 0:
                self.cooldown_counter -= 1
                self.shield_level = self.shield_level * 0.8 
                self.shield_active = True
            else:
                self.shield_level = 0.0
                self.shield_active = False
            
        collapse_res = self.engine.calculate_topological_collapse(data_10d)
        is_collapsed = collapse_res.get("is_collapsed", False)
        
        return {
            'deformation': current_ricci,
            'z_score_reverso': z_score_absoluto,
            'shield_active': self.shield_active,
            'shield_level': self.shield_level,
            'is_collapsed': is_collapsed,
            'qrw_entropy': stochastic_entropy
        }

    def analyze_historical_danger(self, df_slice: pd.DataFrame, threshold: float = 2.5):
        if len(df_slice) < self.danger_window:
            return np.zeros(len(df_slice))
            
        data_10d = np.zeros((10, len(df_slice)))
        data_10d[0, :] = df_slice['open'].values
        data_10d[1, :] = df_slice['high'].values
        data_10d[2, :] = df_slice['low'].values
        data_10d[3, :] = df_slice['close'].values
        data_10d[4, :] = df_slice.get('tick_volume', pd.Series(np.ones(len(df_slice)))).values
        data_10d[5, :] = df_slice['close'].pct_change().fillna(0).values
        data_10d[6, :] = (df_slice['high'] - df_slice['low']).values
        data_10d[7, :] = np.abs(df_slice['close'] - df_slice['open']).values
        data_10d[8, :] = (df_slice['high'] - np.maximum(df_slice['open'], df_slice['close'])).values
        data_10d[9, :] = (np.minimum(df_slice['open'], df_slice['close']) - df_slice['low']).values
        
        return self.engine.calculate_danger_zones(data_10d, self.danger_window, threshold)

if __name__ == "__main__":
    print("Yield Governor ASI-5 (AdS/CFT) module loaded.")