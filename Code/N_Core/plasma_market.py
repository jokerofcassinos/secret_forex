import numpy as np
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
# Prioriza binários compilados
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))
sys.path.append(current_dir)

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
    N-Core Agent: Magnetohydrodynamics (MHD) Ph.D. Edition
    Modela o mercado como um Plasma Magnetizado.
    Preço = Velocidade do Fluido (v)
    Volume/Momentum = Campo Magnético (B)
    """
    def __init__(self, grid_size=128):
        try:
            # Mu: Permeabilidade Magnética Institucional (1.0 = Normal)
            # Resistivity: Baixa para regime MHD Ideal
            self.engine = mhd_engine.MHDIdealEngine(size=grid_size, mu=1.2, resistivity=1e-4)
            self.is_active = True
        except (NameError, AttributeError):
            self.is_active = False
            
        self.in_zone = False
        self.zone_type = None 
        self.state_history = []
        self.current_state = None

    def scan_for_plasma_zones(self, df_slice, lookback=150):
        """
        Identifica zonas de alta densidade de liquidez (Holographic Scan).
        """
        if len(df_slice) < lookback:
            return {'top_level': 0, 'bottom_level': 0, 'top_density': 1, 'bottom_density': 1}

        recent = df_slice.tail(lookback)
        atr = (recent['high'] - recent['low']).mean()
        highs = recent['high'].values
        lows = recent['low'].values
        
        margin = atr * 0.5
        
        top_clusters = []
        bottom_clusters = []
        
        for p in highs[-50:]:
            count = np.sum((highs > p - margin) & (highs < p + margin))
            top_clusters.append((p, count))
            
        for p in lows[-50:]:
            count = np.sum((lows > p - margin) & (lows < p + margin))
            bottom_clusters.append((p, count))
            
        best_top = max(top_clusters, key=lambda x: x[1])
        best_bottom = max(bottom_clusters, key=lambda x: x[1])
        
        return {
            'top_level': best_top[0],
            'top_density': max(1.5, best_top[1] * 0.8),
            'bottom_level': best_bottom[0],
            'bottom_density': max(1.5, best_bottom[1] * 0.8),
            'atr': atr
        }

    def process_tick(self, curr_candle, prev_candle, plasma_zones, dt=0.01):
        """
        Avança a simulação MHD Ideal.
        """
        if not self.is_active: return 0.0, "NO_DATA", {}

        curr_price = curr_candle['close']
        delta_price = curr_price - prev_candle['close']
        vol = curr_candle.get('tick_volume', 100)
        atr = plasma_zones.get('atr', 1.0)
        
        # 1. Determinação da Posição Relativa na Zona de Plasma
        top = plasma_zones['top_level']
        bottom = plasma_zones['bottom_level']
        
        # Define um horizonte de influência (1.5 ATR acima/abaixo)
        horizon = atr * 2.0
        range_min = bottom - horizon
        range_max = top + horizon
        
        # Normalização do preço para a malha C++ (0.0 a 1.0)
        price_norm = (curr_price - range_min) / (range_max - range_min + 1e-9)
        price_norm = np.clip(price_norm, 0.0, 1.0)
        
        # 2. Máquina de Estados de Zona
        dist_top = abs(curr_price - top)
        dist_bottom = abs(curr_price - bottom)
        threshold_dist = atr * 0.7
        
        in_top_plasma = dist_top < threshold_dist
        in_bottom_plasma = dist_bottom < threshold_dist

        if (in_top_plasma or in_bottom_plasma) and not self.in_zone:
            self.in_zone = True
            self.zone_type = "TOP_SWEEP" if in_top_plasma else "BOTTOM_SWEEP"
            self.engine.reset_state()
        elif not in_top_plasma and not in_bottom_plasma and self.in_zone:
            self.in_zone = False
            self.zone_type = None

        # 3. Execução do Motor MHD
        # Injeta: v_inst (momentum), b_inst (volume), p_inst (volatilidade/pressão)
        # Usamos volume logarítmico para escala de campo B
        b_inst = np.log1p(vol) * (1.0 if delta_price >= 0 else -1.0)
        v_inst = delta_price / (atr + 1e-9)
        p_inst = atr * 10.0 # Pressão térmica baseada na volatilidade
        
        self.engine.inject_flux(price_norm, v_inst, b_inst, p_inst)
        
        # Evolução temporal das equações de Maxwell-Navier-Stokes
        state = self.engine.evolve(dt)
        self.current_state = state
        
        # Sinalização
        signal = self.zone_type if self.zone_type else "NEUTRAL"
        if state.magnetic_reconnection:
            signal = "MAGNETIC_RECONNECTION"
            
        metrics = {
            'beta': state.avg_beta,
            'v_alfven': state.max_alfven_velocity,
            'stability': state.magnetic_stability,
            'p_mag': state.magnetic_pressure,
            'tension': state.magnetic_tension
        }
        
        return state.magnetic_stability, signal, metrics

    def get_state(self):
        return self.current_state

if __name__ == "__main__":
    print("MHD Ideal Engine v3.0 (Ph.D.) - N-Core Online.")
