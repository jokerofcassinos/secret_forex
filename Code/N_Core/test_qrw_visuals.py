import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Code.N_Core.quantum_walk import QRWTracker

def test_qrw_visuals():
    print("Iniciando simulação visual: Quantum Random Walk (QRW) - Timeframe H2")
    
    data_path_h1 = os.path.join("Data", "Historical", "GER40.cash_H1.parquet")
    if os.path.exists(data_path_h1):
         print(f"Carregando {data_path_h1} e re-amostrando para H2...")
         df_h1 = pd.read_parquet(data_path_h1)
         df = df_h1.iloc[::2].reset_index(drop=True)
         df = df.tail(1000).reset_index(drop=True)
    else:
         print("Usando dados sintéticos (H2).")
         dates = pd.date_range('2023-01-01', periods=1000, freq='2h')
         
         # Gerar mercado com uma forte consolidação simulada com acúmulo invisível
         prices = 18000 + np.cumsum(np.random.randn(1000) * 10)
         
         # Forçar um range com forte acumulação bullish (preço não sai do lugar, mas candles positivos têm mais volume)
         for i in range(500, 700):
             prices[i] = 18200 + (np.random.rand() * 50 - 25) # Range travado de 50 pontos
         
         highs = prices + np.random.rand(1000) * 10
         lows = prices - np.random.rand(1000) * 10
         volumes = np.random.randint(500, 5000, 1000)
         
         # Aumentar volume escondido apenas nos ticks positivos durante a consolidação
         for i in range(500, 700):
             if prices[i] > prices[i-1]:
                 volumes[i] *= 4 # Interferência construtiva de compra oculta
                 
         df = pd.DataFrame({'time': dates, 'open': prices, 'high': highs, 'low': lows, 'close': prices, 'tick_volume': volumes})
    
    # Adicionar open pro caso sintético
    if 'open' not in df.columns:
        df['open'] = df['close'].shift(1).fillna(df['close'])

    tracker = QRWTracker(positions=201)
    
    if not tracker.is_active:
        print("Erro: Motor C++ QRW não carregado.")
        return

    skewness_list = []
    signals = []
    is_ranging_list = []
    
    LOOKBACK = 20
    
    for i in range(len(df)):
        if i < LOOKBACK:
            skewness_list.append(0.0)
            signals.append("NEUTRAL")
            is_ranging_list.append(False)
            continue
            
        df_slice = df.iloc[i - LOOKBACK + 1 : i + 1]
        
        is_range = tracker.is_in_range(df_slice, lookback=LOOKBACK, atr_threshold=5.0)
        is_ranging_list.append(is_range)
        
        if is_range:
            skew, signal = tracker.process_qrw_skewness(df_slice, lookback=LOOKBACK)
        else:
            skew, signal = 0.0, "NEUTRAL"
            
        skewness_list.append(skew)
        signals.append(signal)
            
    # --- RENDERIZAÇÃO ---
    print("Renderizando Gráfico de Interferência Quântica...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot 1: Preço
    ax1.plot(df.index, df['close'], color='cyan', linewidth=1, label='Ação do Preço (GER40)')
    
    # Marcar Range e Sinal
    for i in range(len(signals)):
        if is_ranging_list[i]:
            ax1.axvspan(i-0.5, i+0.5, color='grey', alpha=0.1, lw=0)
        if signals[i] == "HIDDEN_ACCUMULATION_BULL":
            ax1.scatter(i, df['low'].iloc[i] - 10, color='lime', marker='^', s=50)
        elif signals[i] == "HIDDEN_DISTRIBUTION_BEAR":
            ax1.scatter(i, df['high'].iloc[i] + 10, color='red', marker='v', s=50)
            
    ax1.set_title('Aethelgard Q-MATH: Quantum Random Walk (QRW Decrypter)', color='white')
    ax1.legend(facecolor='black', labelcolor='white')
    
    # Plot 2: QRW Skewness
    ax2.plot(df.index, skewness_list, color='gold', linewidth=1.5, label='Assimetria da Probabilidade (Skewness)')
    ax2.axhline(1.0, color='lime', linestyle=':', label='Threshold Acumulação Bullish (+1.0)')
    ax2.axhline(-1.0, color='red', linestyle=':', label='Threshold Distribuição Bearish (-1.0)')
    ax2.axhline(0.0, color='grey', linestyle='-', linewidth=0.5)
    
    ax2.fill_between(df.index, skewness_list, 1.0, where=(np.array(skewness_list) > 1.0), color='lime', alpha=0.4)
    ax2.fill_between(df.index, skewness_list, -1.0, where=(np.array(skewness_list) < -1.0), color='red', alpha=0.4)
    
    ax2.set_ylabel('Wave Skewness', color='lightgrey')
    ax2.legend(facecolor='black', labelcolor='white', loc='upper right')
    
    # Estilização
    for ax in [ax1, ax2]:
        ax.set_facecolor('#121212')
        ax.tick_params(colors='lightgrey')
        ax.set_xlim(LOOKBACK, len(df))
    fig.patch.set_facecolor('#121212')
    plt.tight_layout()
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "QRW_Interference_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"[SUCESSO] Renderização QRW salva em: {output_path}")

if __name__ == "__main__":
    test_qrw_visuals()
