import numpy as np
import pandas as pd
import sys
import os

# Add the bin/ or built extension path to sys.path so we can import schrodinger_engine
# (This assumes the .pyd or .so is built and placed in the correct location)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine')) # If built in place

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
    N-Core Agent: Quantum Cloud Tracker (Schrödinger Equation)
    Transforms price action into a Probability Cloud to predict Institutional Squeezes and Tunneling.
    """
    def __init__(self, price_min, price_max, bins=500):
        self.price_min = price_min
        self.price_max = price_max
        self.bins = bins
        self.dx = (price_max - price_min) / bins
        
        # Initialize C++ Solver
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
        """
        Initializes the quantum wave packet at the current price.
        Sigma controls the uncertainty (spread of the cloud).
        """
        if not self.is_active: return
        
        if sigma is None:
            sigma = self.dx * 10 # Default uncertainty
            
        x0 = current_price - self.price_min
        self.solver.initialize_gaussian(x0, sigma, k0)

    def generate_potential_from_volume_profile(self, df_slice):
        """
        Translates Order Flow / Volume Profile into a 'Potential Energy' well.
        High Volume Node = Low Potential (Attracts price).
        Low Volume Node = High Potential Barrier (Repels price, requires tunneling).
        """
        V = np.ones(self.bins) * 10.0 # High base potential
        
        # Calculate a simple volume profile
        if 'tick_volume' in df_slice.columns:
            vol_col = 'tick_volume'
        elif 'volume' in df_slice.columns:
            vol_col = 'volume'
        else:
            # Fallback if no volume data
            return list(V)
            
        # Distribute volume into bins
        for i in range(len(df_slice)):
            candle = df_slice.iloc[i]
            c_price = candle['close']
            vol = candle[vol_col]
            idx = self.price_to_index(c_price)
            
            # The more volume, the deeper the potential well (minimum 0.1)
            # This is a simplified approach; can be enhanced with actual Order Book data
            V[idx] = max(0.1, V[idx] - (vol * 0.001)) 
            
        # Smooth the potential using a simple moving average window
        V_smoothed = np.convolve(V, np.ones(5)/5, mode='same')
        return list(V_smoothed)

    def step(self, df_slice, dt=1.0):
        """
        Advances the quantum simulation based on the current market state.
        """
        if not self.is_active: return None
        
        # Calculate Mass (Inverse of Volatility)
        high_low = df_slice['high'] - df_slice['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        
        if np.isnan(atr) or atr == 0:
            mass = 1.0
        else:
            mass = 1.0 / atr  # High ATR -> Low Mass -> Wave spreads faster
            
        # 1. Update Potential Map based on recent history
        V = self.generate_potential_from_volume_profile(df_slice)
        self.solver.update_potential(V)
        
        # 2. Step the PDE forward
        self.solver.step_forward(dt, mass)
        
        # 3. Retrieve Probability Density (Zero-Copy)
        density = self.solver.get_probability_density()
        
        return density
        
    def check_tunneling_signal(self, current_price, resistance_price, density):
        """
        Analyzes the cloud to see if probability density has 'leaked' through a resistance,
        indicating an imminent breakout before price actually moves there.
        """
        curr_idx = self.price_to_index(current_price)
        res_idx = self.price_to_index(resistance_price)
        
        # If the resistance is above us
        if res_idx > curr_idx:
            # Sum probability beyond the resistance
            prob_beyond = np.sum(density[res_idx:])
            # Sum probability trapped behind resistance
            prob_trapped = np.sum(density[curr_idx:res_idx])
            
            if prob_beyond > prob_trapped * 0.5: # Arbitrary tunneling threshold
                return "QUANTUM_TUNNEL_BULL"
        
        # If the resistance is below us (Support)
        elif res_idx < curr_idx:
            prob_beyond = np.sum(density[:res_idx])
            prob_trapped = np.sum(density[res_idx:curr_idx])
            
            if prob_beyond > prob_trapped * 0.5:
                return "QUANTUM_TUNNEL_BEAR"
                
        return "STABLE"

if __name__ == "__main__":
    print("Quantum Clouds module loaded. Awaiting C++ Engine integration.")
