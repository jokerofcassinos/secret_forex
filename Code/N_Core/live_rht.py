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
                return "OFFLINE", []
            
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
            
            # Normalização Robusta: Evita divisão por zero e Infinitos
            mean = log_returns.rolling(20).mean()
            std = log_returns.rolling(20).std().replace(0, 1e-9).fillna(1e-9)
            z_score = (log_returns - mean) / std
            
            # Clipping de Outliers Quânticos (> 4 sigma)
            z_score = np.clip(z_score, -4.0, 4.0)
            tensor_matrix.append(z_score.fillna(0).values)
            
        tensor_matrix = np.array(tensor_matrix, dtype=np.float64)
        num_tf, t_steps = tensor_matrix.shape
        
        # 5. Evolução Termodinâmica no C++
        if self.rht_engine_instance is None:
            self.rht_engine_instance = rht_engine.RHTEngine(num_tf, t_steps)
            
        self.rht_engine_instance.load_tensor_data(tensor_matrix)
        
        # Retorna Histórico de Calor para o HUD
        heat_history = self.rht_engine_instance.compute_resonance_history(gamma=0.15)
        
        # Analisa Estado Instantâneo (Flash Point)
        heat, entropy, direction, flash = self.rht_engine_instance.analyze_current_state(threshold=threshold)
        
        # Formata cache visual para o MT5
        # 1 = Bull Ignition, 2 = Bear Ignition, 0 = Neutral
        rht_cache = []
        for h in heat_history:
            if h > threshold: rht_cache.append("1")
            elif h < -threshold: rht_cache.append("2")
            else: rht_cache.append("0")
            
        # Telemetria de Status
        status = "RHT_LAMINAR"
        if flash == 1.0: status = "RHT_BULL_IGNITION"
        elif flash == -1.0: status = "RHT_BEAR_IGNITION"
        elif abs(heat) > threshold * 0.5: status = "RHT_HEATING"
        
        # Gera histórico de flashes baseado no calor histórico (Consistência com Bars do MT5)
        flash_hist = []
        for h in heat_history:
            f_code = "0"
            if h > threshold * 1.1: f_code = "1"
            elif h < -threshold * 1.1: f_code = "2"
            flash_hist.append(f_code)
            
        return status, rht_cache, flash, ",".join(flash_hist)

if __name__ == "__main__":
    # Teste rápido de ignição
    if mt5.initialize():
        tracker = LiveRHTTracker(symbol="GER40.cash")
        status, cache = tracker.process_live_rht()
        print(f"🔥 RHT STATUS: {status} | Cache Size: {len(cache)}")
        mt5.shutdown()
