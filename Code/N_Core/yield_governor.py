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

    def monitor_topology(self, df_slice: pd.DataFrame):
        """
        Recebe as últimas barras, constrói a Matriz de 10 Dimensões (Features)
        e avalia o Tensor de Ricci em tempo real.
        """
        if len(df_slice) < self.danger_window:
            return {'deformation': 0.0, 'shield_active': False, 'shield_level': 0.0, 'is_collapsed': False}

        # 1. Feature Matrix Extraction (10D Tensor para Ricci)
        # 0: Open, 1: High, 2: Low, 3: Close, 4: Tick Volume, 
        # 5: Return Close, 6: Volatility, 7: Body, 8: UpperWick, 9: LowerWick
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

        # Avalia a gravidade atual baseada no Z-Score reverso dinâmico
        recent_window = ricci_scalar[-self.danger_window:]
        mean_ricci = np.mean(recent_window)
        std_ricci = np.std(recent_window) + 1e-9
        
        current_ricci = ricci_scalar[-1]
        
        # Z-Score Absoluto: Captura poços gravitacionais (negativos) e explosões na métrica (positivos)
        z_score_absoluto = abs(current_ricci - mean_ricci) / std_ricci
        
        # O Threshold dinâmico escala com a volatilidade ATR
        atr = data_10d[6, -self.danger_window:].mean()
        if atr < 1e-9: atr = 1.0
        
        # HISTERESE TOPOLÓGICA (ASI-5)
        # Se Z-Score > 2.5, Shield Ativa e reseta o cooldown.
        if z_score_absoluto > 2.5:
            self.shield_level = min(1.0, (z_score_absoluto - 2.5) / 2.0)
            self.shield_active = True
            self.cooldown_counter = 5 # A gravidade demora 5 barras para se curar
        else:
            if self.cooldown_counter > 0:
                self.cooldown_counter -= 1
                self.shield_level = self.shield_level * 0.8 # Decaimento suave do shield
                self.shield_active = True
            else:
                self.shield_level = 0.0
                self.shield_active = False
            
        collapse_res = self.engine.calculate_topological_collapse(data_10d)
        is_collapsed = collapse_res.get("is_collapsed", False)
        
        return {
            'deformation': current_ricci,
            'z_score_reverso': z_score_absoluto, # Mantido o nome da chave por compatibilidade
            'shield_active': self.shield_active,
            'shield_level': self.shield_level,
            'is_collapsed': is_collapsed
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