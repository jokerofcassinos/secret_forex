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
    N-Core Agent: Quantum Cloud Tracker v3.0 (Gaussian Gravity Wells)
    FIX P0-05/P0-06: Absorbing boundaries + adaptive dt + wave recentering.
    HIGH-FIDELITY: Uses Gaussian smoothed potential for sharp wave collapse.
    """
    def __init__(self, price_min, price_max, bins=512):
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
            sigma = self.dx * 12
        x0 = current_price - self.price_min
        self.solver.initialize_gaussian(x0, sigma, k0)

    def generate_potential_from_volume_profile(self, df_slice):
        """
        HIGH-FIDELITY v7: Ultra-Deep Gravity Wells.
        Forced compression for SEC singularity triggers.
        """
        V_base = 200.0  
        
        vol_col = 'tick_volume' if 'tick_volume' in df_slice.columns else 'volume'
        if vol_col not in df_slice.columns:
            return [V_base] * self.bins
            
        vol_array = df_slice[vol_col].astype(np.float64).values
        vol_mean = np.mean(vol_array) if len(vol_array) > 0 else 1000.0
        # Increased scale for deeper wells
        vol_scale = 150.0 / (vol_mean + 1e-9)
            
        highs = df_slice['high'].values
        lows = df_slice['low'].values
        n_candles = len(df_slice)
        
        # SOVEREIGN decay: Prioritize recent activity
        decay_factor = np.exp(np.linspace(-2.0, 0, n_candles))
        
        strength_map = np.zeros(self.bins, dtype=np.float64)
        
        for i in range(n_candles):
            mid_p = (highs[i] + lows[i]) / 2.0
            range_p = max(self.dx * 5.0, highs[i] - lows[i]) 
            idx_mid = self.price_to_index(mid_p)
            
            width_bins = int(range_p / self.dx * 1.5) + 1
            i_start = max(0, idx_mid - width_bins)
            i_end = min(self.bins, idx_mid + width_bins)
            
            x = np.arange(i_start, i_end)
            dist = (x - idx_mid) * self.dx
            
            strength = (vol_array[i] * vol_scale) * decay_factor[i]
            well_shape = strength * np.exp(-1.5 * (dist / (range_p + 1e-9))**2)
            strength_map[i_start:i_end] += well_shape
            
        # Deeper potential for localization
        V = np.maximum(2.0, V_base - strength_map)
        
        V_smoothed = np.convolve(V, np.ones(5)/5, mode='same')
        return list(V_smoothed)

    def step(self, df_slice, dt=0.2, steps=1):
        if not self.is_active: return None
        
        # Dynamic Re-centering (Safe margin)
        curr_price = df_slice['close'].iloc[-1]
        needs_reset = False
        if curr_price < self.price_min + (self.price_max - self.price_min) * 0.1 or \
           curr_price > self.price_max - (self.price_max - self.price_min) * 0.1:
            center = curr_price
            half_range = (self.price_max - self.price_min) / 2.0
            self.price_min = center - half_range
            self.price_max = center + half_range
            self.dx = (self.price_max - self.price_min) / self.bins
            self.solver = schrodinger_engine.QuantumCloudSolver(self.bins, self.dx)
            self.initialize_wave(curr_price)
            needs_reset = True

        com_price = self.index_to_price(self.solver.get_center_of_mass())
        price_dist = abs(curr_price - com_price)
        
        last_close = df_slice['close'].iloc[-2] if len(df_slice) > 1 else df_slice['close'].iloc[-1]
        tr = max(df_slice['high'].iloc[-1] - df_slice['low'].iloc[-1], abs(df_slice['high'].iloc[-1] - last_close), abs(df_slice['low'].iloc[-1] - last_close))
        
        # HEAVY MASS (DAMPING): Prevent high-frequency vertical noise
        base_mass = 200.0 / (tr + 1e-5)
        if price_dist > tr * 2.0:
            mass = base_mass * 0.1 # Dynamic sync
        else:
            mass = base_mass
            
        mass = max(1.0, min(5000.0, mass))

        V = self.generate_potential_from_volume_profile(df_slice)
        self.solver.update_potential(V)
        
        for _ in range(steps):
            self.solver.step_forward(dt, mass)
        
        x0 = curr_price - self.price_min
        # Stable wave width
        sigma = self.dx * 15
        self.solver.recenter_wave(x0, sigma * 1.5)
        
        density = self.solver.get_probability_density()
        return density, needs_reset
        
    def get_gravity_well_price(self, density):
        if density is None: return None
        max_idx = np.argmax(density)
        return self.index_to_price(max_idx)

    def get_singularity_metrics(self):
        if not self.is_active: return None
        return self.solver.calculate_singularity_metrics(self.price_min, self.price_max)

    def check_quantum_tunneling(self, barrier_energy, particle_energy, volume_mass):
        if not self.is_active: return 0.0
        return self.solver.calculate_tunneling_probability(barrier_energy, particle_energy, volume_mass)

    def check_tunneling_signal(self, current_price, resistance_price, density):
        curr_idx = self.price_to_index(current_price)
        res_idx = self.price_to_index(resistance_price)
        if res_idx > curr_idx:
            prob_beyond = np.sum(density[res_idx:])
            prob_trapped = np.sum(density[curr_idx:res_idx])
            if prob_beyond > prob_trapped * 0.5: return "QUANTUM_TUNNEL_BULL"
        elif res_idx < curr_idx:
            prob_beyond = np.sum(density[:res_idx])
            prob_trapped = np.sum(density[res_idx:curr_idx])
            if prob_beyond > prob_trapped * 0.5: return "QUANTUM_TUNNEL_BEAR"
        return "STABLE"

if __name__ == "__main__":
    print("Quantum Clouds v3.0 [HIGH-FIDELITY] loaded.")
