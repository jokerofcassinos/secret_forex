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
    import qrw_engine
except ImportError as e:
    print(f"WARNING: qrw_engine C++ module not found. Error: {e}")

class QRWTracker:
    """
    N-Core Agent: Quantum Random Walk (QRW)
    Decodes hidden accumulation/distribution inside ranges using quantum coin interference.
    """
    def __init__(self, positions=201):
        try:
            self.engine = qrw_engine.QRWEngine(positions)
            self.is_active = True
        except NameError:
            self.is_active = False

    def is_in_range(self, df_slice, lookback=20, atr_threshold=5.0):
        """
        Determines if the market is currently ranging (consolidating).
        """
        recent = df_slice.tail(lookback)
        high_max = recent['high'].max()
        low_min = recent['low'].min()
        box_height = high_max - low_min
        
        # Calculate ATR
        tr1 = df_slice['high'] - df_slice['low']
        tr2 = np.abs(df_slice['high'] - df_slice['close'].shift())
        tr3 = np.abs(df_slice['low'] - df_slice['close'].shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # If the whole box is smaller than 1.5x the ATR, we are in a tight range
        return box_height < (atr * atr_threshold)

    def process_qrw_skewness(self, df_slice, lookback=20):
        """
        Calculates the skewness of the quantum probability wave.
        Returns: (skewness, signal)
        """
        if not self.is_active or len(df_slice) < lookback:
            return 0.0, "NONE"
            
        recent = df_slice.tail(lookback).copy()
        price_deltas = (recent['close'] - recent['open']).values
        volumes = recent.get('tick_volume', pd.Series(np.ones(lookback))).values
        
        # Compute skewness using C++ engine
        skewness = self.engine.compute_interference_skew(list(price_deltas), list(volumes))
        
        signal = "NEUTRAL"
        if skewness > 1.0:
            signal = "HIDDEN_ACCUMULATION_BULL"
        elif skewness < -1.0:
            signal = "HIDDEN_DISTRIBUTION_BEAR"
            
        return skewness, signal

if __name__ == "__main__":
    print("QRW Decrypter module loaded.")