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
    import mhd_engine
except ImportError as e:
    print(f"WARNING: mhd_engine C++ module not found. Error: {e}")

class PlasmaMarketTracker:
    """
    N-Core Agent: Magnetohydrodynamics (MHD) Z-Pinch
    Models stop hunt zones as Plasma and institutional momentum as Magnetic Fields.
    Predicts the exact tick of a liquidity sweep reversal (Z-Pinch collapse).
    """
    def __init__(self):
        try:
            self.engine = mhd_engine.MHDEngine(mu=1.5, adiabatic_idx=1.666)
            self.is_active = True
        except NameError:
            self.is_active = False
            
        self.in_zone = False
        self.zone_type = None # "BULL" (Resistance sweep) or "BEAR" (Support sweep)
        self.z_index_history = []

    def scan_for_plasma_zones(self, df_slice, lookback=100):
        """
        Identifies major liquidity pools (Plasma).
        """
        highs = df_slice['high'].iloc[-lookback:-5]
        lows = df_slice['low'].iloc[-lookback:-5]
        
        major_high = highs.max()
        major_low = lows.min()
        
        # Calculate zone density (how many times price touched near the level)
        high_touches = len(highs[highs > major_high * 0.999])
        low_touches = len(lows[lows < major_low * 1.001])
        
        return {
            'top_level': major_high,
            'top_density': max(1.0, high_touches),
            'bottom_level': major_low,
            'bottom_density': max(1.0, low_touches)
        }

    def process_tick(self, curr_candle, prev_candle, plasma_zones):
        """
        Advances the MHD simulation.
        """
        if not self.is_active: return 0.0, "NO_DATA"

        curr_price = curr_candle['close']
        delta_price = curr_price - prev_candle['close']
        vol = curr_candle.get('tick_volume', 100)
        
        # Check if we entered a plasma zone (Stop Hunt region)
        margin = (plasma_zones['top_level'] - plasma_zones['bottom_level']) * 0.05
        
        entered_top = curr_price > (plasma_zones['top_level'] - margin)
        entered_bottom = curr_price < (plasma_zones['bottom_level'] + margin)

        if entered_top and not self.in_zone:
            self.in_zone = True
            self.zone_type = "TOP_SWEEP"
            self.engine.reset_state()
            
        elif entered_bottom and not self.in_zone:
            self.in_zone = True
            self.zone_type = "BOTTOM_SWEEP"
            self.engine.reset_state()
            
        elif not entered_top and not entered_bottom and self.in_zone:
            self.in_zone = False
            self.zone_type = None
            self.engine.reset_state()

        if self.in_zone:
            z_density = plasma_zones['top_density'] if self.zone_type == "TOP_SWEEP" else plasma_zones['bottom_density']
            z_idx = self.engine.step_pinch(delta_price, vol, z_density)
            self.z_index_history.append(z_idx)
            return z_idx, self.zone_type
            
        return 0.0, "NEUTRAL"

    def get_z_index_history(self):
        return self.z_index_history

if __name__ == "__main__":
    print("Plasma Market (MHD) module loaded.")