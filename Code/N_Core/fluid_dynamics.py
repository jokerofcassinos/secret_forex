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
    N-Core Agent: LBM Fluid Dynamics
    Models the market as a compressible fluid to predict Squeezes and Ruptures.
    """
    def __init__(self, price_min, price_max, bins=500, tau=0.8):
        self.price_min = price_min
        self.price_max = price_max
        self.bins = bins
        self.dx = (price_max - price_min) / bins
        
        try:
            self.engine = lbm_engine.LBMEngine(self.bins, tau)
            self.is_active = True
        except NameError:
            self.is_active = False

    def price_to_index(self, price):
        idx = int((price - self.price_min) / self.dx)
        return max(0, min(idx, self.bins - 1))
        
    def index_to_price(self, idx):
        return self.price_min + (idx * self.dx)

    def process_tick_stream(self, df_slice, steps=10):
        """
        Injects recent price action into the fluid grid and runs the LBM steps.
        """
        if not self.is_active: return None, None
        
        # Inject mass and momentum
        for i in range(len(df_slice)):
            candle = df_slice.iloc[i]
            c_price = candle['close']
            vol = candle.get('tick_volume', 100)
            
            is_green = candle['close'] >= candle['open']
            momentum = 1.0 if is_green else -1.0
            
            # Normalize mass injection
            mass = vol * 0.001
            
            idx = self.price_to_index(c_price)
            self.engine.inject_liquidity(idx, mass, momentum)
            
        # Run BGK Collision and Streaming
        for _ in range(steps):
            self.engine.step()
            
        density = self.engine.get_density()
        velocity = self.engine.get_velocity()
        
        return np.array(density), np.array(velocity)

    def detect_squeeze_rupture(self, current_price, density, velocity):
        """
        Scans for zones with extremely high density (compression)
        and high absolute velocity (directional aggression).
        Returns a signal if a rupture is imminent.
        """
        curr_idx = self.price_to_index(current_price)
        
        # Check local neighborhood (e.g. +/- 5 bins)
        start = max(0, curr_idx - 5)
        end = min(self.bins, curr_idx + 6)
        
        local_density = np.mean(density[start:end])
        local_velocity = np.mean(velocity[start:end])
        
        global_mean_density = np.mean(density)
        
        # Rupture thresholds (can be optimized by reinforcement learning later)
        if local_density > global_mean_density * 2.0:
            if local_velocity > 0.5: # Bullish Rupture
                return "FLUID_RUPTURE_BULL"
            elif local_velocity < -0.5: # Bearish Rupture
                return "FLUID_RUPTURE_BEAR"
                
        return "LAMINAR_FLOW"

if __name__ == "__main__":
    print("LBM Fluid Dynamics module loaded.")