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
    import schrodinger_engine
except ImportError as e:
    print(f"WARNING: schrodinger_engine C++ module not found or DLL missing. Error: {e}")

class QuantumCloudTracker:
    """
    N-Core Agent: Quantum Cloud Tracker v2.0 (Schrödinger Equation)
    FIX P0-05/P0-06: Absorbing boundaries + adaptive dt + wave recentering.
    FIX P1-05: Volume distributed across candle range, not single bin.
    """
    def __init__(self, price_min, price_max, bins=500):
        self.price_min = price_min
        self.price_max = price_max
        self.bins = bins
        self.dx = (price_max - price_min) / bins
        
        try:
            self.solver = schrodinger_engine.QuantumCloudSolver(self.bins, self.dx)
            self.is_active = True
        except NameError:
            self.is_active = False
            
    def price_to_index(self, price):
        idx = int((price - self.price_min) / self.dx)
        return max(0, min(idx, self.bins - 1))
        
    def index_to_price(self, idx):
        return self.price_min + (idx * self.dx)

    def initialize_wave(self, current_price, sigma=None, k0=0.0):
        if not self.is_active: return
        if sigma is None:
            sigma = self.dx * 10
        x0 = current_price - self.price_min
        self.solver.initialize_gaussian(x0, sigma, k0)

    def generate_potential_from_volume_profile(self, df_slice):
        """
        FIX P1-05: Volume now distributed across the entire candle range (high-low),
        not just assigned to the close bin.
        """
        V = np.ones(self.bins) * 10.5  # Stable base potential for Crank-Nicolson

        if 'tick_volume' in df_slice.columns:
            vol_col = 'tick_volume'
        elif 'volume' in df_slice.columns:
            vol_col = 'volume'
        else:
            return list(V)
            
        # FIX OVERFLOW: Use float64 for sum/mean and avoid int32 overflow
        vol_array = df_slice[vol_col].astype(np.float64).values
        vol_mean = np.mean(vol_array) if len(vol_array) > 0 else 1000.0
        vol_scale = 0.5 / (vol_mean + 1e-9)
            
        records = df_slice.to_dict('records')
        for candle in records:
            vol = float(candle.get(vol_col, 0.0))
            
            # FIX P1-05: Distribute volume across the candle's full range
            idx_low = self.price_to_index(candle['low'])
            idx_high = self.price_to_index(candle['high'])
            
            if idx_high <= idx_low:
                idx_high = idx_low + 1
            
            n_bins_covered = idx_high - idx_low
            vol_per_bin = vol / max(1, n_bins_covered)
            
            for b in range(idx_low, min(idx_high + 1, self.bins)):
                # Deepen the well significantly based on volume
                V[b] = max(0.0, V[b] - (vol_per_bin * vol_scale))
            
        V_smoothed = np.convolve(V, np.ones(5)/5, mode='same')
        return list(V_smoothed)

    def step(self, df_slice, dt=1.0):
        if not self.is_active: return None
        
        # Calculate True Range ATR (FIX P1-10 consistency)
        high_low = df_slice['high'] - df_slice['low']
        high_close = np.abs(df_slice['high'] - df_slice['close'].shift(1))
        low_close = np.abs(df_slice['low'] - df_slice['close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # FIX: Mass is now significantly heavier so the wave doesn't disperse instantly
        # Mass calibrated to ATR for natural fluidity
        if np.isnan(atr) or atr < 1e-9:
            mass = 1.0
        else:
            mass = 1.0 / atr

        V = self.generate_potential_from_volume_profile(df_slice)
        self.solver.update_potential(V)
        
        # FIX P0-06: step_forward now handles adaptive substeps internally
        self.solver.step_forward(dt, mass)
        
        # Recentering is now handled gracefully inside C++ (only if completely lost)
        current_price = df_slice['close'].iloc[-1]
        x0 = current_price - self.price_min
        sigma = self.dx * 10
        self.solver.recenter_wave(x0, sigma)
        
        density = self.solver.get_probability_density()
        return density
        
    def get_gravity_well_price(self, density):
        """
        Returns the price at the peak of the probability density.
        FIX P0-10: Provides a reliable gravity well based on corrected cloud.
        """
        if density is None:
            return None
        max_idx = np.argmax(density)
        return self.index_to_price(max_idx)

    def check_tunneling_signal(self, current_price, resistance_price, density):
        curr_idx = self.price_to_index(current_price)
        res_idx = self.price_to_index(resistance_price)
        
        if res_idx > curr_idx:
            prob_beyond = np.sum(density[res_idx:])
            prob_trapped = np.sum(density[curr_idx:res_idx])
            if prob_beyond > prob_trapped * 0.5:
                return "QUANTUM_TUNNEL_BULL"
        elif res_idx < curr_idx:
            prob_beyond = np.sum(density[:res_idx])
            prob_trapped = np.sum(density[res_idx:curr_idx])
            if prob_beyond > prob_trapped * 0.5:
                return "QUANTUM_TUNNEL_BEAR"
                
        return "STABLE"

if __name__ == "__main__":
    print("Quantum Clouds v2.0 module loaded.")
