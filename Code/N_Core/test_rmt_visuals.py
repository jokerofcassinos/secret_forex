import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Code.N_Core.random_matrix import RandomMatrixTracker

def test_rmt_spectral_filter():
    print("Iniciando simulação visual: RMT Spectral Filter (Filtro de Ruído Varejo) - Timeframe H2")
    
    data_path = os.path.join("Data", "Historical", "BTCUSD_H2.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Tentando H1 ou sintético.")
        data_path_h1 = os.path.join("Data", "Historical", "BTCUSD_H1.parquet")
        if os.path.exists(data_path_h1):
             print(f"Carregando {data_path_h1} e re-amostrando para H2...")
             df_h1 = pd.read_parquet(data_path_h1)
             df = df_h1.iloc[::2].reset_index(drop=True)
             df = df.tail(1000).reset_index(drop=True)
        else:
             print("Usando dados sintéticos (H2).")
             dates = pd.date_range('2023-01-01', periods=1000, freq='2h')
             
             # Gerar mercado consolidado (Ruído) e depois uma forte agressão institucional
             prices = 18000 + np.cumsum(np.random.randn(1000) * 15)
             # Inserir "Pernadas Institucionais" (Baixo Ruído, Alta Direção e Volume) no meio e fim
             for i in range(400, 450): prices[i] += (i - 400) * 12
             for i in range(800, 850): prices[i] -= (i - 800) * 15
             
             highs = prices + np.random.rand(1000) * 15
             lows = prices - np.random.rand(1000) * 15
             volumes = np.random.randint(500, 5000, 1000)
             # Volume salta nas pernadas institucionais
             volumes[400:450] *= 5
             volumes[800:850] *= 5
             
             df = pd.DataFrame({'time': dates, 'open': prices, 'high': highs, 'low': lows, 'close': prices, 'tick_volume': volumes})
    else:
        print(f"Carregando {data_path}...")
        df = pd.read_parquet(data_path)
        df = df.tail(1000).reset_index(drop=True)
        
    T_STEPS = 100
    tracker = RandomMatrixTracker(time_steps=T_STEPS)
    
    if not tracker.is_active:
        print("Erro: Motor C++ RMT não carregado.")
        return

    power_ratios = []
    signals = []
    
    for i in range(len(df)):
        if i < T_STEPS:
            power_ratios.append(0.0)
            signals.append(False)
            continue
            
        df_slice = df.iloc[i - T_STEPS + 1 : i + 1]
        lambda_dom, power_ratio, is_pure = tracker.process_spectral_filter(df_slice)
        
        power_ratios.append(power_ratio)
        signals.append(is_pure)
            
    # --- RENDERIZAÇÃO ---
    print("Renderizando Gráfico Espectral...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot 1: Preço com Fundo Colorido onde há Sinal Puro
    ax1.plot(df.index, df['close'], color='cyan', linewidth=1, label='Ação do Preço (GER40)')
    
    # Preencher fundo onde o sinal é Institucional (>2x o Ruído de Marchenko-Pastur)
    for i in range(len(signals)):
        if signals[i]:
            ax1.axvspan(i-0.5, i+0.5, color='lime', alpha=0.3, lw=0)
            
    ax1.set_title('Aethelgard Q-MATH: Teoria de Matrizes Aleatórias (RMT Noise Filter)', color='white')
    ax1.legend(facecolor='black', labelcolor='white')
    
    # Plot 2: RMT Power Ratio
    ax2.plot(df.index, power_ratios, color='magenta', linewidth=1.5, label='Signal Power Ratio ($\lambda_1 / \lambda_{max}$)')
    ax2.axhline(1.0, color='grey', linestyle='--', label='Limite Marchenko-Pastur (Ruído Máximo)')
    ax2.axhline(2.0, color='lime', linestyle=':', label='Threshold de Institucional Puro (>2.0)')
    
    ax2.fill_between(df.index, power_ratios, 1.0, where=(np.array(power_ratios) > 1.0), color='magenta', alpha=0.2)
    ax2.fill_between(df.index, power_ratios, 2.0, where=(np.array(power_ratios) > 2.0), color='lime', alpha=0.4)
    
    ax2.set_ylabel('Power Ratio', color='lightgrey')
    ax2.legend(facecolor='black', labelcolor='white', loc='upper right')
    ax2.set_ylim(0, max(max(power_ratios) * 1.1, 3.0))
    
    # Estilização
    for ax in [ax1, ax2]:
        ax.set_facecolor('#121212')
        ax.tick_params(colors='lightgrey')
        ax.set_xlim(T_STEPS, len(df))
    fig.patch.set_facecolor('#121212')
    plt.tight_layout()
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "RMT_Spectrum_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"[SUCESSO] Renderização Espectral RMT salva em: {output_path}")

if __name__ == "__main__":
    test_rmt_spectral_filter()
