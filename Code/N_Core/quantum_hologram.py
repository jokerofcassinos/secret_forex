import os
import sys
import numpy as np
import pandas as pd

# Adiciona o diretório do C++ Engine ao path para importar a biblioteca compilada
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CPP_Engine')))

# Adiciona o path do Mingw64 para o Python 3.8+ conseguir achar as DLLs do C++ (libstdc++, etc)
if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    except FileNotFoundError:
        pass

import rht_engine

class QuantumHologramNezus:
    def __init__(self, symbol="US100.cash", data_dir=r"D:\AI Brain\US30\Data\Historical"):
        self.symbol = symbol
        self.data_dir = data_dir
        self.timeframes = ['M5', 'M15', 'H1', 'H2', 'D1']
        self.data = {}
        
    def load_and_align_fractals(self, lookback_steps=1000):
        """Carrega dados, constrói o fractal H2 e alinha todos no index M5."""
        print(f"[N-Core] Iniciando fusão fractal para {self.symbol}...")
        
        # 1. Carregar base (M5)
        df_m5 = pd.read_parquet(os.path.join(self.data_dir, f"{self.symbol}_M5.parquet"))
        df_m5['time'] = pd.to_datetime(df_m5['time'])
        df_m5.set_index('time', inplace=True)
        df_m5 = df_m5.sort_index()
        
        # Cortar para os últimos N steps baseados no M5 para economizar memória e focar no agora
        df_base = df_m5.iloc[-lookback_steps:][['close']].rename(columns={'close': 'M5_close'})
        
        # 2. Carregar e mesclar outros timeframes (Forward Fill para simular o estado em cada tick do M5)
        tfs_to_load = ['M15', 'H1', 'D1']
        for tf in tfs_to_load:
            df_tf = pd.read_parquet(os.path.join(self.data_dir, f"{self.symbol}_{tf}.parquet"))
            df_tf['time'] = pd.to_datetime(df_tf['time'])
            df_tf.set_index('time', inplace=True)
            df_tf = df_tf.sort_index()
            
            # Reindexar no index base (M5) com forward fill
            df_base = df_base.join(df_tf[['close']].rename(columns={'close': f'{tf}_close'}), how='left')
            df_base[f'{tf}_close'] = df_base[f'{tf}_close'].ffill()

        # 3. Construir o H2 (Mandatório via Regra 5.4) a partir do H1 ou M15
        # Como H2 nem sempre está no MetaTrader como arquivo isolado, vamos resamplar o M5.
        print("[N-Core] Sintetizando Tensor H2 por resample...")
        df_h2 = df_m5['close'].resample('2h').last().dropna().to_frame(name='H2_close')
        df_base = df_base.join(df_h2, how='left')
        df_base['H2_close'] = df_base['H2_close'].ffill()

        # Drop NaN incial por causa do ffill
        df_base = df_base.ffill().bfill()
        self.merged_df = df_base
        print(f"[N-Core] Fusão concluída. Shape da Matriz Temporal: {self.merged_df.shape}")
        
    def compute_tensors(self):
        """Transforma os preços brutos em Ondas de Momentum (Z-Score Local)"""
        print("[N-Core] Processando Ondas de Momentum (Normalização Tensorial por Janela Móvel)...")
        tensor_matrix = []
        
        for tf in self.timeframes:
            col = f"{tf}_close"
            # Calcula o retorno percentual como onda base
            returns = self.merged_df[col].pct_change().fillna(0)
            
            # Normalização Z-Score Local (Rolling Window de 20 períodos)
            rolling_mean = returns.rolling(window=20, min_periods=1).mean()
            rolling_std = returns.rolling(window=20, min_periods=1).std().replace(0, 1).fillna(1)
            
            z_score = (returns - rolling_mean) / rolling_std
            z_score = z_score.fillna(0) # Primeiro tick terá NaN
                
            tensor_matrix.append(z_score.values)
            
        # Matriz final: (Num_Timeframes, Time_Steps)
        self.tensor_matrix = np.array(tensor_matrix, dtype=np.float64)
        
    def run_holographic_resonance(self):
        """Injeta os tensores no C++ e verifica o colapso de função de onda"""
        num_tf, t_steps = self.tensor_matrix.shape
        print(f"[Q-Math Bridge] Injetando matriz {num_tf}x{t_steps} no motor RHT (C++)...")
        
        # Inicializa o motor C++
        rht = rht_engine.RHTEngine(num_tf, t_steps)
        rht.load_tensor_data(self.tensor_matrix)
        
        # Calcula a ressonância no instante final (Agente operando ao vivo)
        resonance, direction, collapse_flag = rht.get_instant_collapse(threshold=0.6) # Threshold de gravidade
        
        print("\n" + "="*50)
        print("====== RESULTADO DO COLAPSO HOLOGRÁFICO ======")
        print("="*50)
        print(f"Ressonância Final: {resonance:.4f} (Energia)")
        
        dir_str = "BULL (Alta)" if direction > 0 else "BEAR (Baixa)" if direction < 0 else "NEUTRAL"
        print(f"Vetor Direcional : {dir_str}")
        
        if collapse_flag == 1.0:
            print(">>> ESTADO DE COLAPSO: [ BUY / LONG ] - Interferência Construtiva Bullish Validada.")
        elif collapse_flag == -1.0:
            print(">>> ESTADO DE COLAPSO: [ SELL / SHORT ] - Interferência Construtiva Bearish Validada.")
        else:
            print(">>> ESTADO DE COLAPSO: [ PURIFYING ] - Ruído de Mercado. Sem convergência fractal.")
        print("="*50)

if __name__ == "__main__":
    hologram = QuantumHologramNezus()
    hologram.load_and_align_fractals(lookback_steps=5000) # Últimos 5000 ticks do M5
    hologram.compute_tensors()
    hologram.run_holographic_resonance()
