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
    N-Core Agent: Quantum Cloud Tracker v3.4 (Gaussian Gravity Wells)
    v24.1: Institutional Attraction & Doppler Effect.
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
            sigma = self.dx * 35 # Expandido v24.1
        sigma = max(self.dx * 5.0, sigma)
        x0 = current_price - self.price_min
        x0 = max(self.dx * 5.0, min(x0, (self.bins - 5) * self.dx))
        self.solver.initialize_gaussian(x0, sigma, k0)

    def generate_potential_from_volume_profile(self, df_slice):
        V_base = 100.0  
        vol_col = 'tick_volume' if 'tick_volume' in df_slice.columns else 'volume'
        if vol_col not in df_slice.columns: return [V_base] * self.bins
        vol_array = df_slice[vol_col].astype(np.float64).values
        vol_mean = np.mean(vol_array) if len(vol_array) > 0 else 1000.0
        vol_scale = 80.0 / (vol_mean + 1e-9) 
        
        highs = df_slice['high'].values
        lows = df_slice['low'].values
        n_candles = len(df_slice)
        decay_lambda = 0.02 
        decay_factor = np.exp(-decay_lambda * np.arange(n_candles)[::-1])
        strength_map = np.zeros(self.bins, dtype=np.float64)
        for i in range(n_candles):
            mid_p = (highs[i] + lows[i]) / 2.0
            range_p = max(self.dx * 3.0, highs[i] - lows[i]) 
            idx_mid = self.price_to_index(mid_p)
            width_bins = int(range_p / self.dx * 2.0) + 1
            i_start = max(0, idx_mid - width_bins)
            i_end = min(self.bins, idx_mid + width_bins)
            x = np.arange(i_start, i_end)
            dist = (x - idx_mid) * self.dx
            strength = (vol_array[i] * vol_scale) * decay_factor[i]
            well_shape = strength * np.exp(-2.0 * (dist / (range_p + 1e-9))**2)
            strength_map[i_start:i_end] += well_shape
        V = np.maximum(5.0, V_base - strength_map)
        V_smoothed = np.convolve(V, np.ones(3)/3, mode='same')
        return list(V_smoothed)

    def step(self, df_slice, dt=0.2, steps=1, pti=0.0):
        if not self.is_active: return None
        
        tr = (df_slice['high'] - df_slice['low']).rolling(14).mean().iloc[-1]
        if np.isnan(tr) or tr < self.dx: tr = self.dx * 10.0
        
        # v25.3: QUANTUM BLOOM (hbar=12.0) para fusão de fatias
        hbar_dynamic = max(12.0, min(30.0, tr / (self.dx * 1.0)))

        # 1. SMOOTH GRID SHIFTING
        curr_price = df_slice['close'].iloc[-1]
        margin = (self.price_max - self.price_min) * 0.20
        
        if curr_price < self.price_min + margin:
            shift_dist = (self.price_max - self.price_min) * 0.3
            steps_shift = int(shift_dist / self.dx)
            self.price_min -= steps_shift * self.dx
            self.price_max = self.price_min + (self.bins * self.dx)
            self.solver.shift_grid(-steps_shift)
        elif curr_price > self.price_max - margin:
            shift_dist = (self.price_max - self.price_min) * 0.3
            steps_shift = int(shift_dist / self.dx)
            self.price_min += steps_shift * self.dx
            self.price_max = self.price_min + (self.bins * self.dx)
            self.solver.shift_grid(steps_shift)

        com_price = self.index_to_price(self.solver.get_center_of_mass())
        price_dist = abs(curr_price - com_price)
        
        # 2. MASS GUARD
        base_mass = 200.0 / (tr + 1e-5)
        mass = base_mass * 0.1 if price_dist > tr * 2.0 else base_mass
        mass = max(5.0, min(2000.0, mass))

        V = self.generate_potential_from_volume_profile(df_slice)
        
        vol_col = 'tick_volume' if 'tick_volume' in df_slice.columns else 'volume'
        vol_profile = df_slice[vol_col].values if vol_col in df_slice.columns else np.ones(len(df_slice))
        atr_rel = tr / (df_slice['high'].max() - df_slice['low'].min() + 1e-9)
        mass_scale_factor = 1.0 / (1.0 + atr_rel * 50.0) 
        global_mass = mass * mass_scale_factor
        
        # ACOPLAMENTO MASSA-PREÇO v25.0 (SUPERFLUIDEZ)
        # Se PTI elevado (exaustão), a nuvem derrete para seguir o preço instantaneamente
        if pti > 0.85:
            global_mass *= 0.05
            
        spatial_mass = np.ones(self.bins, dtype=np.float64)
        visc_cap = 5.0 / (len(df_slice) + 1e-9)
        
        for i in range(len(df_slice)):
            mid_p = (df_slice['high'].iloc[i] + df_slice['low'].iloc[i]) / 2.0
            idx = self.price_to_index(mid_p)
            local_viscosity = (df_slice[vol_col].iloc[i] / (np.mean(vol_profile) + 1e-9)) * visc_cap
            x = np.arange(self.bins)
            dist = (x - idx) * self.dx
            spatial_mass += local_viscosity * np.exp(-3.0 * (dist / (tr + 1e-9))**2)
            
        spatial_mass = np.clip(spatial_mass, 0.5, 5.0) 
        
        self.solver.update_potential(V)
        self.solver.update_spatial_mass(list(spatial_mass))
        
        # 3. DRIFT MOMENTUM
        price_velocity = (df_slice['close'].iloc[-1] - df_slice['close'].iloc[-2]) if len(df_slice) > 1 else 0.0
        drift_k = np.clip(price_velocity / (self.dx * 5.0), -0.3, 0.3)
        drift_k *= 1.2 # v25.1: Compensação de advecção para Trail contínuo
        
        # 4. EVOLUTION STEP
        for _ in range(steps):
            self.solver.step_forward(dt, global_mass, hbar_dynamic, drift_k)
        
        # v25.4: REMOVIDA RECENTRALIZAÇÃO HARD (Causa do 'efeito pipoca')
        # A onda agora flui naturalmente seguindo o poço de gravidade e o momentum.
        
        density = self.solver.get_probability_density()
        return density, False
        
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
    print("Quantum Clouds v3.4 [ATTRACTION] loaded.")
