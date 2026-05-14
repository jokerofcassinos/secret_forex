import numpy as np
import pandas as pd
import sys
import os

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e diretórios base
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")

if os.name == 'nt':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    if os.path.exists(root_path):
        os.add_dll_directory(root_path)
    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)

if root_path not in sys.path:
    sys.path.insert(0, root_path)
if bin_path not in sys.path:
    sys.path.insert(0, bin_path)

try:
    import lbm_engine
except ImportError as e:
    print(f"WARNING: lbm_engine C++ module not found. Error: {e}")

class LBMFluidDynamics:
    """
    N-Core Agent: LBM Fluid Dynamics v5.0 (ASI-5)
    Utiliza Smagorinsky Subgrid Turbulence Model e Número de Reynolds dinâmico.
    Aniquila thresholds estatísticos de Z-Score. Opera com Gradientes de Pressão.
    """
    def __init__(self, price_min, price_max, bins=200, smagorinsky_cs=0.15):
        self.price_min = price_min
        self.price_max = price_max
        self.bins = bins
        self.dx = (price_max - price_min) / bins
        
        try:
            self.engine = lbm_engine.LBMEngine(self.bins, 1.0, smagorinsky_cs)
            self.is_active = True
        except NameError:
            self.is_active = False

    def price_to_index(self, price):
        idx = int((price - self.price_min) / self.dx)
        return max(0, min(idx, self.bins - 1))
        
    def index_to_price(self, idx):
        return self.price_min + (idx * self.dx)

    def process_tick_stream(self, df_slice, steps=10):
        if not self.is_active: return None, None, None, None
        
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
            
            # Massa proporcional ao volume relativo
            mass_weight = np.clip(vol / avg_vol, 0.5, 3.0)
            
            body = candle['close'] - candle['open']
            momentum = np.clip(body / (atr + 1e-9), -0.45, 0.45)
            
            mass = (vol * 0.001) * mass_weight
            idx = self.price_to_index(c_price)
            self.engine.inject_liquidity(idx, mass, float(momentum))
            
        for _ in range(steps):
            self.engine.step()
            
        density = np.array(self.engine.get_density())
        velocity = np.array(self.engine.get_velocity())
        pressure = np.array(self.engine.get_pressure())
        reynolds = np.array(self.engine.get_reynolds())
        
        # --- PROTOCOLO DE DESFRIBILAÇÃO NEXUS ---
        if np.any(np.isnan(density)) or np.any(np.isinf(density)) or (len(density) > 0 and np.max(density) > 1e8):
            print("⚠️ LBM ENGINE: Instabilidade termodinâmica detectada. Reiniciando o motor de fluidos.")
            import lbm_engine
            self.engine = lbm_engine.LBMEngine(self.bins, 1.0, 0.15)
            density = np.zeros(self.bins)
            velocity = np.zeros(self.bins)
            pressure = np.zeros(self.bins)
            reynolds = np.zeros(self.bins)
            
        return density, velocity, pressure, reynolds

    def detect_squeeze_rupture(self, df_slice, density, velocity, pressure, reynolds, current_regime=0):
        """
        NEXUS TQFM v5.0 :: LBM Smagorinsky Turbulency Detection.
        Elimina Z-Scores. Avalia o número de Reynolds e Diferença de Pressão.
        """
        if len(df_slice) < 50: return "LAMINAR_FLOW"
        if density is None or pressure is None: return "LAMINAR_FLOW"
        
        current_price = df_slice['close'].iloc[-1]
        curr_idx = self.price_to_index(current_price)
        
        # 1. Âncora de Range e ATR
        lookback = 30
        local_range = df_slice.iloc[-lookback:]
        r_high = local_range['high'].max()
        r_low = local_range['low'].min()
        atr = (df_slice['high'] - df_slice['low']).rolling(14).mean().iloc[-1]
        
        # 2. Análise Termodinâmica Local
        start = max(0, curr_idx - 2)
        end = min(self.bins, curr_idx + 3)
        
        local_pressure = np.max(pressure[start:end])
        local_velocity = np.mean(velocity[start:end])
        local_reynolds = np.max(reynolds[start:end])
        
        mean_pressure = np.mean(pressure)
        
        # 3. ASI-5 FÍSICA DE FLUIDOS
        # Pressão Rompe Coesão: P_local >> P_media * Fator de Coesão
        cohesion_factor = 2.0 
        is_pressure_rupture = (local_pressure > mean_pressure * cohesion_factor)
        
        # Turbulência ou Condensado? (Baseado em Reynolds)
        # Re baixo = Viscoso/Laminar (Condensando energia)
        # Re alto = Turbulência/Dispersão de Fônons
        
        if is_pressure_rupture:
            # Alta Pressão + Turbulência Direcional = Ruptura (Explosão fluida)
            if local_reynolds > 5.0: # Limiar de turbulência empírico
                if local_velocity > 0.05:
                    if current_regime != 2 or current_price <= r_low + atr * 0.3:
                        return "FLUID_RUPTURE_BULL"
                elif local_velocity < -0.05:
                    if current_regime != 1 or current_price >= r_high - atr * 0.3:
                        return "FLUID_RUPTURE_BEAR"
            
            # Alta Pressão + Escoamento Laminar (Baixo Reynolds) = Squeeze Bosônico
            # A energia está presa, coagulando antes de explodir.
            if local_reynolds <= 5.0 and abs(local_velocity) < 0.05:
                return "BOSONIC_SQUEEZE"
                
        return "LAMINAR_FLOW"

    def evaluate_viscoelastic_shock(self, anomaly_duration_seconds):
        if not self.is_active: return False
        return self.engine.is_viscoelastic_absorption(anomaly_duration_seconds)

if __name__ == "__main__":
    print("LBM Fluid Dynamics v5.0 (Smagorinsky/Reynolds) module loaded.")