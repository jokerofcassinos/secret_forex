import os
import sys
import numpy as np
import pandas as pd
import MetaTrader5 as mt5

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CPP_Engine')))
if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    except FileNotFoundError:
        pass

import rht_engine

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
        
    def process_live_rht(self, threshold=0.6):
        """Puxa dados ao vivo, alinha tensores e processa no C++"""
        dfs = {}
        
        # 1. Obter dados live
        for name, tf in self.timeframes.items():
            # M5 precisa do lookback inteiro. D1 precisa de menos, mas puxamos igual para facilitar.
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, self.lookback)
            if rates is None or len(rates) == 0:
                return None, None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            dfs[name] = df[['close']].rename(columns={'close': f'{name}_close'})

        # 2. Alinhamento pelo M5 (Base)
        df_base = dfs['M5']
        
        for name in ['M15', 'H1', 'D1']:
            df_base = df_base.join(dfs[name], how='left')
            df_base[f'{name}_close'] = df_base[f'{name}_close'].ffill()

        # 3. H2 Sintético Mandatório
        df_h2 = dfs['M5']['M5_close'].resample('2h').last().dropna().to_frame(name='H2_close')
        df_base = df_base.join(df_h2, how='left')
        df_base['H2_close'] = df_base['H2_close'].ffill()

        df_base = df_base.ffill().bfill()

        # 4. Z-Score Tensorial (Rolling 20)
        tensor_matrix = []
        ordered_tfs = ['M5', 'M15', 'H1', 'H2', 'D1']
        
        for tf in ordered_tfs:
            col = f"{tf}_close"
            returns = df_base[col].pct_change().fillna(0)
            rolling_mean = returns.rolling(window=20, min_periods=1).mean()
            rolling_std = returns.rolling(window=20, min_periods=1).std().replace(0, 1).fillna(1)
            z_score = (returns - rolling_mean) / rolling_std
            tensor_matrix.append(z_score.fillna(0).values)
            
        tensor_matrix = np.array(tensor_matrix, dtype=np.float64)
        num_tf, t_steps = tensor_matrix.shape
        
        # 5. C++ RHT Engine
        rht = rht_engine.RHTEngine(num_tf, t_steps)
        rht.load_tensor_data(tensor_matrix)
        resonance_history = rht.compute_resonance() # Retorna array
        
        resonance_arr = np.array(resonance_history)
        
        # Gera o cache visual para o MQL5 (1 = Bull Collapse, 2 = Bear Collapse, 0 = Neutral)
        rht_cache = []
        for res in resonance_arr:
            if res > threshold:
                rht_cache.append("1")
            elif res < -threshold:
                rht_cache.append("2")
            else:
                rht_cache.append("0")
                
        # Status atual
        curr_res = resonance_arr[-1]
        status = "PURIFYING"
        if curr_res > threshold:
            status = "RHT_BULL_COLLAPSE"
        elif curr_res < -threshold:
            status = "RHT_BEAR_COLLAPSE"
            
        return status, rht_cache
