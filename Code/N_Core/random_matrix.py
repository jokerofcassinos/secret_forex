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
    N-Core Agent: Random Matrix Theory (RMT)
    Filters out retail noise using Eigenvalue Decomposition and Marchenko-Pastur distribution.
    """
    def __init__(self, time_steps=100):
        # Features: [Returns, Spread, Vol, Body, UpWick, LowWick, Entropy, LBM]
        self.N_FEATURES = 8
        self.T = time_steps
        self.engine = None
        
        try:
            self.engine = rmt_engine.RMTEngine(self.N_FEATURES, self.T)
            self.is_active = True
        except NameError:
            self.is_active = False

    def build_feature_matrix(self, df_slice, lbm_velocity=None):
        """
        Converts the raw dataframe into an expanded multi-dimensional feature matrix.
        """
        if len(df_slice) != self.T:
            return None
            
        returns = df_slice['close'].pct_change().fillna(0).values
        spreads = (df_slice['high'] - df_slice['low']).values
        volumes = df_slice.get('tick_volume', pd.Series(np.ones(self.T))).values
        bodies = np.abs(df_slice['close'] - df_slice['open']).values
        upper_wicks = (df_slice['high'] - np.maximum(df_slice['open'], df_slice['close'])).values
        lower_wicks = (np.minimum(df_slice['open'], df_slice['close']) - df_slice['low']).values
        
        # New Quantum Features:
        # 1. Volatility Entropy (ATR Normalized)
        vol_entropy = (spreads / (df_slice['close'].rolling(20).std().bfill() + 1e-9)).values
        
        # 2. LBM Fluid Interaction
        if lbm_velocity is None:
            lbm_v_arr = np.zeros(self.T)
        else:
            lbm_v_arr = np.array(lbm_velocity) if len(lbm_velocity) == self.T else np.zeros(self.T)
            
        matrix = np.vstack([
            returns, spreads, volumes, bodies, 
            upper_wicks, lower_wicks, vol_entropy, lbm_v_arr
        ])
        return matrix

    def process_spectral_filter(self, df_slice, lbm_velocity=None):
        """
        Calculates the Spectral Signature of institutional mass.
        """
        if not self.is_active or len(df_slice) < self.T:
            return 0.0, 0.0, False
            
        matrix = self.build_feature_matrix(df_slice.tail(self.T), lbm_velocity)
        if matrix is None: return 0.0, 0.0, False
        
        # Re-instantiate engine if dimensions don't match (Safety Lock)
        if self.engine is None or matrix.shape[0] != self.N_FEATURES:
            self.N_FEATURES = matrix.shape[0]
            self.engine = rmt_engine.RMTEngine(self.N_FEATURES, self.T)
            
        self.engine.load_data(matrix)
        
        # Spectral Extraction
        lambda_dom, power_ratio, lambda_max_mp = self.engine.extract_dominant_eigenvalue()
        
        # RMT v2.0 Decision Threshold:
        # Calibrado para 2.5x o limite de Marchenko-Pastur (Noise Floor)
        is_pure_signal = power_ratio > 2.5
        
        return lambda_dom, power_ratio, is_pure_signal

if __name__ == "__main__":
    print("RMT Spectral Filter module loaded.")