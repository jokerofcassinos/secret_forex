import os
import sys
import numpy as np
import pandas as pd
import MetaTrader5 as mt5

# [BOOTLOADER] Força reconhecimento dos binários e Engines C++
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")

for p in [root_path, bin_path]:
    if os.path.exists(p):
        if hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(p)
            except Exception: pass
        if p not in sys.path:
            sys.path.insert(0, p)

try:
    import rht_engine
except ImportError:
    print("⚠️ RHT_ENGINE .pyd não encontrado. Recompilação necessária.")

class LiveRHTTracker:
    def __init__(self, symbol="US100.cash", lookback=300):
        self.symbol = symbol
        self.lookback = lookback
        self.timeframes = {
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'D1': mt5.TIMEFRAME_D1
        }
        self.rht_engine_instance = None
        
    def process_live_rht(self, threshold=0.7):
        """Puxa dados ao vivo, alinha tensores e processa no motor termodinâmico C++"""
        dfs = {}
        
        # 1. Extração de Dados Multi-Fractais
        for name, tf in self.timeframes.items():
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, self.lookback)
            if rates is None or len(rates) == 0:
                return f"OFFLINE_{name}", [], 0.0, ""
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            dfs[name] = df[['close']].rename(columns={'close': f'{name}_close'})

        # 2. Alinhamento Topológico (Base M5)
        df_base = dfs['M5']
        for name in ['M15', 'H1', 'D1']:
            df_base = df_base.join(dfs[name], how='left')
            df_base[f'{name}_close'] = df_base[f'{name}_close'].ffill()

        # 3. Timeframe H2 (Sintético - AdS/CFT Horizon)
        df_h2 = dfs['M5']['M5_close'].resample('2h').last().dropna().to_frame(name='H2_close')
        df_base = df_base.join(df_h2, how='left')
        df_base['H2_close'] = df_base['H2_close'].ffill()

        # Limpeza de Singularidades (NaN)
        df_base = df_base.ffill().bfill().tail(self.lookback)

        # 4. Cálculo de Momentum Tensorial (Z-Score)
        tensor_matrix = []
        ordered_tfs = ['M5', 'M15', 'H1', 'H2', 'D1']
        
        for tf in ordered_tfs:
            col = f"{tf}_close"
            # Momentum logarítmico para estabilidade termodinâmica
            log_returns = np.log(df_base[col] / df_base[col].shift(1)).fillna(0)
            
            # [v38.1] Normalização Time-Absolute (48 horas reais) em vez de N barras.
            # Impede a distorção gravitacional entre M5 e D1.
            mean = log_returns.rolling('48h', min_periods=5).mean()
            std = log_returns.rolling('48h', min_periods=5).std().replace(0, 1e-9).fillna(1e-9)
            z_score = (log_returns - mean) / std
            
            # Clipping de Outliers Quânticos (> 4 sigma)
            z_score = np.clip(z_score, -4.0, 4.0)
            tensor_matrix.append(z_score.fillna(0).values)
            
        tensor_matrix = np.array(tensor_matrix, dtype=np.float64)
        num_tf, t_steps = tensor_matrix.shape
        
        # 5. Evolução Termodinâmica no C++ (ASI v3.0)
        if self.rht_engine_instance is None:
            self.rht_engine_instance = rht_engine.RHTEngine(num_tf, t_steps)
            
        self.rht_engine_instance.load_tensor_data(tensor_matrix)
        
        # Sincronização Termodinâmica Contínua
        self.rht_engine_instance.compute_thermodynamics(0.15) 
        
        # Coleta do Tensor Completo
        hist = self.rht_engine_instance.get_thermodynamics()
        heat_flux = hist.get("heat_flux", [])
        entropy_field = hist.get("entropy", [])
        ignition_state = hist.get("ignition", [])
        
        # Estado Atual (Flash Point)
        heat = heat_flux[-1] if len(heat_flux) > 0 else 0.0
        entropy = entropy_field[-1] if len(entropy_field) > 0 else 1.0
        flash = ignition_state[-1] if len(ignition_state) > 0 else 0.0
        
        # Formata cache visual para o MT5
        rht_cache = []
        for h in heat_flux:
            if h > threshold: rht_cache.append("1")
            elif h < -threshold: rht_cache.append("2")
            else: rht_cache.append("0")
            
        # Telemetria de Status Ph.D.
        status = "RHT_LAMINAR"
        if flash == 1.0: status = "RHT_BULL_CONDENSATE"
        elif flash == -1.0: status = "RHT_BEAR_CONDENSATE"
        elif abs(heat) > threshold * 0.5: status = "RHT_TURBULENCE"
        
        # Histórico Termodinâmico Espectral
        flash_hist = []
        for h, ent in zip(heat_flux, entropy_field):
            f_code = "0"
            if h > threshold and ent < 0.4: f_code = "1"
            elif h < -threshold and ent < 0.4: f_code = "2"
            flash_hist.append(f_code)
            
        return status, rht_cache, flash, ",".join(flash_hist), heat_flux, entropy_field

if __name__ == "__main__":
    # Teste rápido de ignição
    if mt5.initialize():
        tracker = LiveRHTTracker(symbol="GER40.cash")
        status, cache = tracker.process_live_rht()
        print(f"🔥 RHT STATUS: {status} | Cache Size: {len(cache)}")
        mt5.shutdown()
