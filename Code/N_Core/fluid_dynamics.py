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
    import lbm_engine
except ImportError as e:
    print(f"WARNING: lbm_engine C++ module not found. Error: {e}")

class LBMFluidDynamics:
    """
    N-Core Agent: LBM Fluid Dynamics v2.0
    FIX P0-08: tau >= 1.0 for stability.
    FIX P0-09: Momentum proportional to candle body strength.
    FIX P1-09: Mass decay built into C++ engine.
    """
    def __init__(self, price_min, price_max, bins=200, tau=1.0):
        self.price_min = price_min
        self.price_max = price_max
        self.bins = bins
        self.dx = (price_max - price_min) / bins
        
        try:
            # FIX P0-08: Default tau=1.0 for guaranteed stability
            self.engine = lbm_engine.LBMEngine(self.bins, max(1.0, tau))
            self.is_active = True
        except NameError:
            self.is_active = False

    def price_to_index(self, price):
        idx = int((price - self.price_min) / self.dx)
        return max(0, min(idx, self.bins - 1))
        
    def index_to_price(self, idx):
        return self.price_min + (idx * self.dx)

    def process_tick_stream(self, df_slice, steps=10):
        if not self.is_active: return None, None
        
        # Calculate ATR for momentum normalization
        tr = df_slice['high'] - df_slice['low']
        atr = tr.rolling(min(14, len(df_slice))).mean().iloc[-1]
        if np.isnan(atr) or atr < 1e-9:
            atr = 1.0
        
        for i in range(len(df_slice)):
            candle = df_slice.iloc[i]
            c_price = candle['close']
            vol = candle.get('tick_volume', 100)
            
            body = candle['close'] - candle['open']
            
            # FIX P0-09: Momentum proportional to body size normalized by ATR
            # Range: approximately -0.3 to +0.3 (clamped in C++)
            momentum = np.clip(body / (atr + 1e-9), -0.3, 0.3)
            
            mass = vol * 0.001
            idx = self.price_to_index(c_price)
            self.engine.inject_liquidity(idx, mass, float(momentum))
            
        for _ in range(steps):
            self.engine.step()
            
        density = self.engine.get_density()
        velocity = self.engine.get_velocity()
        
        return np.array(density), np.array(velocity)

    def detect_squeeze_rupture(self, current_price, density, velocity):
        curr_idx = self.price_to_index(current_price)
        start = max(0, curr_idx - 5)
        end = min(self.bins, curr_idx + 6)
        
        local_density = np.mean(density[start:end])
        local_velocity = np.mean(velocity[start:end])
        global_mean_density = np.mean(density)
        
        if local_density > global_mean_density * 2.0:
            if local_velocity > 0.1:
                return "FLUID_RUPTURE_BULL"
            elif local_velocity < -0.1:
                return "FLUID_RUPTURE_BEAR"
                
        return "LAMINAR_FLOW"

if __name__ == "__main__":
    print("LBM Fluid Dynamics v2.0 module loaded.")