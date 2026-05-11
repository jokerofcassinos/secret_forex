import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ancorar na raiz
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(ROOT_DIR, 'Code'))

from N_Core.live_rht import LiveRHTTracker

def test_rht_thermodynamics():
    print("Iniciando auditoria visual: RHT Thermodynamics ASI v3.0")
    
    # Vamos gerar dados sintéticos hiper-realistas para provar o motor fractal
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=800, freq='5min')
    prices = 18000 + np.cumsum(np.random.randn(800) * 8)
    
    # Criar um choque de volatilidade (Flash Point) no meio
    prices[400:450] += np.linspace(0, 300, 50) # Subida forte
    prices[450:500] += np.linspace(300, 0, 50) # Descida
    
    df_m5 = pd.DataFrame({'time': dates, 'close': prices})
    df_m5.set_index('time', inplace=True)
    
    # Simular o comportamento do MT5
    class MockMT5:
        TIMEFRAME_M5 = '5min'
        TIMEFRAME_M15 = '15min'
        TIMEFRAME_H1 = '1h'
        TIMEFRAME_D1 = '1D'
        @staticmethod
        def copy_rates_from_pos(symbol, tf, start, count):
            res = df_m5['close'].resample(tf).last().dropna()
            df_res = pd.DataFrame({'time': res.index.astype(np.int64) // 10**9, 'close': res.values})
            return df_res.to_dict('records')
            
    # Mocking mt5 dependency inside LiveRHTTracker
    import N_Core.live_rht
    N_Core.live_rht.mt5 = MockMT5
    
    tracker = LiveRHTTracker(symbol="SYNTH", lookback=300)
    status, cache, flash, f_hist, heat, entropy = tracker.process_live_rht()
    
    if len(heat) == 0:
        print("Erro ao processar RHT.")
        return
        
    print(f"Status Final: {status}")
    print(f"Calor Máximo Atingido: {np.max(heat):.2f}")
    print(f"Entropia Mínima Atingida: {np.min(entropy):.2f}")
    
    # Plotagem
    fig, ax = plt.subplots(3, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [3, 1, 1]})
    fig.patch.set_facecolor('black')
    
    # 1. Preço M5
    ax[0].set_facecolor('black')
    ax[0].plot(df_m5.index[-300:], df_m5['close'].tail(300), color='cyan', linewidth=1)
    ax[0].set_title('RHT ASI v3.0 - Resonância Fractal Termodinâmica', color='white', fontsize=14)
    ax[0].grid(color='white', alpha=0.1)
    ax[0].tick_params(colors='white')
    
    # 2. Fluxo de Calor (Heat Flux)
    ax[1].set_facecolor('black')
    ax[1].fill_between(range(len(heat)), 0, heat, where=(np.array(heat) > 0), color='cyan', alpha=0.5, label='Bullish Heat')
    ax[1].fill_between(range(len(heat)), 0, heat, where=(np.array(heat) < 0), color='magenta', alpha=0.5, label='Bearish Heat')
    ax[1].plot(heat, color='white', linewidth=1)
    ax[1].set_ylabel('Heat Flux (Q)', color='white')
    ax[1].grid(color='white', alpha=0.1)
    ax[1].tick_params(colors='white')
    ax[1].axhline(0, color='gray', linestyle='--')
    ax[1].legend(facecolor='black', labelcolor='white')
    
    # 3. Entropia de Shannon
    ax[2].set_facecolor('black')
    ax[2].plot(entropy, color='yellow', linewidth=1.5, label='Entropy (S)')
    ax[2].fill_between(range(len(entropy)), 0, entropy, color='yellow', alpha=0.2)
    ax[2].set_ylabel('Shannon Entropy', color='white')
    ax[2].set_ylim(0, 1.1)
    ax[2].grid(color='white', alpha=0.1)
    ax[2].tick_params(colors='white')
    ax[2].legend(facecolor='black', labelcolor='white')
    
    plt.tight_layout()
    
    output_dir = os.path.join(ROOT_DIR, "Docs", "05_Estrutura_Corporativa", "Setores", "R_EXEC")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "RHT_Phd_Audit.png")
    plt.savefig(output_path, dpi=300, facecolor='black')
    print(f"Auditoria Visual salva em: {output_path}")

if __name__ == "__main__":
    test_rht_thermodynamics()
