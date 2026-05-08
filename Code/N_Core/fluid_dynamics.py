import numpy as np
import pandas as pd
import sys
import os

# [BOOTLOADER] Força reconhecimento dos binários Mingw64
if os.name == 'nt' and os.path.exists(r"D:\msys64\mingw64\bin"):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")


try:
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
    def __init__(self, price_min, price_max, bins=200, tau=1.2):
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
        avg_vol = df_slice['tick_volume'].tail(20).mean()
        if np.isnan(atr) or atr < 1e-9: atr = 1.0
        if np.isnan(avg_vol) or avg_vol < 1.0: avg_vol = 100.0
        
        for i in range(len(df_slice)):
            candle = df_slice.iloc[i]
            c_price = candle['close']
            vol = candle.get('tick_volume', 100)
            
            # IMPECÁVEL: Massa proporcional ao volume relativo
            mass_weight = np.clip(vol / avg_vol, 0.5, 3.0)
            
            body = candle['close'] - candle['open']
            momentum = np.clip(body / (atr + 1e-9), -0.15, 0.15)
            
            mass = (vol * 0.001) * mass_weight
            idx = self.price_to_index(c_price)
            self.engine.inject_liquidity(idx, mass, float(momentum))
            
        for _ in range(steps):
            self.engine.step()
            
        density = np.array(self.engine.get_density())
        velocity = np.array(self.engine.get_velocity())
        
        # --- PROTOCOLO DE DESFRIBILAÇÃO NEXUS ---
        if np.any(np.isnan(density)) or np.any(np.isinf(density)) or (len(density) > 0 and np.max(density) > 1e8):
            import lbm_engine
            self.engine = lbm_engine.LBMEngine(self.bins, 1.2)
            density = np.zeros(self.bins)
            velocity = np.zeros(self.bins)
            
        return density, velocity

    def detect_squeeze_rupture(self, df_slice, density, velocity, current_regime=0):
        """
        NEXUS TQFM v4.2 :: POLARITY EXCLUSION & HYSTERESIS.
        Filtra ruídos contraditórios usando o regime macro como âncora de polaridade.
        """
        if len(df_slice) < 50: return "LAMINAR_FLOW"
        
        current_price = df_slice['close'].iloc[-1]
        curr_idx = self.price_to_index(current_price)
        
        # 1. Âncora de Range e ATR
        lookback = 30
        local_range = df_slice.iloc[-lookback:]
        r_high = local_range['high'].max()
        r_low = local_range['low'].min()
        atr = (df_slice['high'] - df_slice['low']).rolling(14).mean().iloc[-1]
        
        # 2. Análise de Massa (Média Móvel de Densidade para Histerese)
        start = max(0, curr_idx - 2)
        end = min(self.bins, curr_idx + 3)
        local_density = np.max(density[start:end])
        local_velocity = np.mean(velocity[start:end])
        
        global_mean_rho = np.mean(density)
        global_std_rho = np.std(density)
        if global_std_rho < 1e-9: global_std_rho = 1e-9
        z_rho = (local_density - global_mean_rho) / global_std_rho
        
        # 3. PROTOCOLO DE EXCLUSÃO MÚTUA ABSOLUTA (TQFM v4.3)
        # Elevamos o threshold de 2.5 para 3.5 para ignorar ruído de varejo.
        # Soberania Total: Proibição de sinais contra-regime em Tsunamis ativos.
        is_extreme_climax = (z_rho > 7.5)
        
        # [BULL RUPTURE]
        if z_rho > 3.5 and local_velocity > 0.05:
            # BLOQUEIO: Se o regime é Bear Tsunami, ignoramos compras a menos que seja um Clímax de Fundo Violento.
            if (current_regime != 2) or (current_price <= r_low + atr * 0.3 and is_extreme_climax):
                if current_price > (r_high + r_low)/2 or local_velocity > 0.15:
                    return "FLUID_RUPTURE_BULL"
        
        # [BEAR RUPTURE]
        if z_rho > 3.5 and local_velocity < -0.05:
            # BLOQUEIO: Se o regime é Bull Tsunami, ignoramos vendas (roxo) a menos que seja um Clímax de Topo Violento.
            if (current_regime != 1) or (current_price >= r_high - atr * 0.3 and is_extreme_climax):
                if current_price < (r_high + r_low)/2 or local_velocity < -0.15:
                    return "FLUID_RUPTURE_BEAR"

        # 4. CLÍMAX DE EXAUSTÃO (Cata-Topos e Cata-Fundos de Alta Precisão)
        if z_rho > 6.0:
            if current_price >= r_high - (atr * 0.15) and local_velocity < -0.05: return "FLUID_RUPTURE_BEAR"
            if current_price <= r_low + (atr * 0.15) and local_velocity > 0.05: return "FLUID_RUPTURE_BULL"

        # 5. BOSONIC SQUEEZE (Compressão de Massa sem Direção Clara)
        if z_rho > 3.2 and abs(local_velocity) < 0.03:
            return "BOSONIC_SQUEEZE"
                
        return "LAMINAR_FLOW"


    def evaluate_viscoelastic_shock(self, anomaly_duration_seconds):
        if not self.is_active: return False
        return self.engine.is_viscoelastic_absorption(anomaly_duration_seconds)


if __name__ == "__main__":
    print("LBM Fluid Dynamics v2.0 module loaded.")