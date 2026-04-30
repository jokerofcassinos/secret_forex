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
        # Features: [Close Returns, High-Low Spread, Tick Volume, Body Size, Upper Wick, Lower Wick]
        self.N_FEATURES = 6 
        self.T = time_steps
        
        try:
            self.engine = rmt_engine.RMTEngine(self.N_FEATURES, self.T)
            self.is_active = True
        except NameError:
            self.is_active = False

    def build_feature_matrix(self, df_slice):
        """
        Converts the raw dataframe into a multi-dimensional feature matrix.
        Shape: (N_FEATURES, T)
        """
        if len(df_slice) != self.T:
            return None
            
        returns = df_slice['close'].pct_change().fillna(0).values
        spreads = (df_slice['high'] - df_slice['low']).values
        volumes = df_slice.get('tick_volume', pd.Series(np.ones(self.T))).values
        bodies = np.abs(df_slice['close'] - df_slice['open']).values
        upper_wicks = (df_slice['high'] - np.maximum(df_slice['open'], df_slice['close'])).values
        lower_wicks = (np.minimum(df_slice['open'], df_slice['close']) - df_slice['low']).values
        
        matrix = np.vstack([returns, spreads, volumes, bodies, upper_wicks, lower_wicks])
        return matrix

    def process_spectral_filter(self, df_slice):
        """
        Calculates the Dominant Eigenvalue to determine Institutional Presence.
        Returns: (eigenvalue, signal_power_ratio, is_pure_signal)
        """
        if not self.is_active or len(df_slice) < self.T:
            return 0.0, 0.0, False
            
        matrix = self.build_feature_matrix(df_slice.tail(self.T))
        if matrix is None: return 0.0, 0.0, False
        
        # Load data into C++ Engine
        self.engine.load_data(matrix)
        
        # Extract Eigenvalue via Power Iteration in C++
        lambda_dom, power_ratio, lambda_max_mp = self.engine.extract_dominant_eigenvalue()
        
        # Se a energia do Sinal Dominante for maior que 2x o limite do Ruído de Varejo (Marchenko-Pastur)
        is_pure_signal = power_ratio > 2.0
        
        return lambda_dom, power_ratio, is_pure_signal

if __name__ == "__main__":
    print("RMT Spectral Filter module loaded.")