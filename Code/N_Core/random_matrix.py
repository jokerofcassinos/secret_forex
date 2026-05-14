import numpy as np
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
    import rmt_engine
except ImportError as e:
    print(f"WARNING: rmt_engine C++ module not found. Error: {e}")

class RandomMatrixTracker:
    """
    N-Core Agent: Random Matrix Theory (RMT) - ASI-5
    Uses Jacobi Spectral Decomposition and Marchenko-Pastur bound to mathematically clip noise.
    """
    def __init__(self, time_steps=100):
        # ASI-5 Features: Expanding dimensionality to satisfy Marchenko-Pastur stability (N >= 8)
        # 1. Close Ret, 2. High Ret, 3. Low Ret, 4. Volatility, 5. Volume, 6. Body, 7. Upper Wick, 8. Lower Wick, 9. Entropy, 10. LBM Flow
        self.N_FEATURES = 10
        self.T = time_steps
        self.engine = None
        
        try:
            self.engine = rmt_engine.RMTEngine(self.N_FEATURES, self.T)
            self.is_active = True
        except NameError:
            self.is_active = False

    def build_feature_matrix(self, df_slice, lbm_velocity=None):
        if len(df_slice) != self.T:
            return None
            
        ret_c = df_slice['close'].pct_change().fillna(0).values
        ret_h = df_slice['high'].pct_change().fillna(0).values
        ret_l = df_slice['low'].pct_change().fillna(0).values
        
        spreads = (df_slice['high'] - df_slice['low']).values
        volumes = df_slice.get('tick_volume', pd.Series(np.ones(self.T))).values
        bodies = np.abs(df_slice['close'] - df_slice['open']).values
        upper_wicks = (df_slice['high'] - np.maximum(df_slice['open'], df_slice['close'])).values
        lower_wicks = (np.minimum(df_slice['open'], df_slice['close']) - df_slice['low']).values
        
        # Volatility Entropy
        vol_entropy = (spreads / (df_slice['close'].rolling(20).std().bfill() + 1e-9)).values
        
        # LBM Fluid Interaction
        if lbm_velocity is None or len(lbm_velocity) < self.T:
            lbm_v_arr = np.zeros(self.T)
        else:
            lbm_v_arr = np.array(lbm_velocity[-self.T:])
            
        matrix = np.vstack([
            ret_c, ret_h, ret_l, spreads, volumes, bodies, 
            upper_wicks, lower_wicks, vol_entropy, lbm_v_arr
        ])
        return matrix

    def process_spectral_filter(self, df_slice, lbm_velocity=None):
        """
        Executa a 'Eigenvalue Clipping' matemática e isola o Sinal Institucional.
        """
        if not self.is_active or len(df_slice) < self.T:
            return "NOISE_DOMINANT"
            
        matrix = self.build_feature_matrix(df_slice.tail(self.T), lbm_velocity)
        if matrix is None: return "NOISE_DOMINANT"
        
        if self.engine is None or matrix.shape[0] != self.N_FEATURES:
            self.N_FEATURES = matrix.shape[0]
            self.engine = rmt_engine.RMTEngine(self.N_FEATURES, self.T)
            
        self.engine.load_data(matrix)
        
        # ASI-5: Spectral Cleaning (Jacobi + MP Limit)
        results = self.engine.perform_spectral_cleaning()
        snr = results.get("signal_to_noise", 0.0)
        power = results.get("signal_power", 0.0)
        
        # Se a proporção Signal-to-Noise é esmagadora (Sinal Puro)
        # O Power deve ultrapassar em pelo menos 1.5x o Limite MP de Caos absoluto
        if snr > 1.2 and power > 1.5:
            return "SIGNAL_ISOLATED"
            
        return "NOISE_DOMINANT"

if __name__ == "__main__":
    print("RMT Spectral Alchemist (ASI-5) loaded.")