import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ensure we can import the agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Code.N_Core.quantum_clouds import QuantumCloudTracker

def test_quantum_clouds():
    print("Iniciando simulação visual: Nuvens de Probabilidade de Schrödinger - Timeframe H2")
    
    data_path = os.path.join("Data", "Historical", "GER40.cash_H2.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Tentando H1 ou sintético.")
        data_path_h1 = os.path.join("Data", "Historical", "GER40.cash_H1.parquet")
        if os.path.exists(data_path_h1):
             print(f"Carregando {data_path_h1} e re-amostrando para H2...")
             df_h1 = pd.read_parquet(data_path_h1)
             df = df_h1.iloc[::2].reset_index(drop=True)
             df = df.tail(200).reset_index(drop=True)
        else:
             print("Usando dados sintéticos (H2).")
             dates = pd.date_range('2023-01-01', periods=200, freq='2h')
             prices = 18000 + np.cumsum(np.random.randn(200) * 15)
             highs = prices + np.random.rand(200) * 10
             lows = prices - np.random.rand(200) * 10
             volumes = np.random.randint(500, 5000, 200)
             df = pd.DataFrame({'time': dates, 'open': prices, 'high': highs, 'low': lows, 'close': prices, 'tick_volume': volumes})
    else:
        print(f"Carregando {data_path}...")
        df = pd.read_parquet(data_path)
        # Pegar apenas uma fatia recente (ex: últimos 200 candles)
        df = df.tail(200).reset_index(drop=True)
    
    price_min = df['low'].min() - 50
    price_max = df['high'].max() + 50
    
    print(f"Range de Preço: {price_min:.2f} a {price_max:.2f}")
    
    tracker = QuantumCloudTracker(price_min=price_min, price_max=price_max, bins=500)
    
    if not tracker.is_active:
        print("Erro: Motor C++ não carregado. Verifique a compilação.")
        return

    # Histórico de densidade para o Heatmap (Dimensão Temporal x Espacial)
    density_history = []
    
    print("Processando fluxo de ticks através da Malha Quântica C++...")
    
    # 1. Inicializar a Nuvem no primeiro preço
    tracker.initialize_wave(df['close'].iloc[0], sigma=(tracker.dx * 15))
    
    # 2. Iterar no tempo para propagar a Equação de Schrödinger
    for i in range(1, len(df)):
        # Criar uma "visão de janela" para calcular o potencial local
        window = max(0, i - 20)
        df_slice = df.iloc[window:i+1]
        
        density = tracker.step(df_slice, dt=1.0)
        
        # O C++ retorna uma referência (Zero-Copy), então precisamos fazer uma cópia 
        # rápida do estado em Numpy para o histórico de plotagem.
        density_history.append(np.array(density))
        
    print("Renderizando Espectrografia Termodinâmica...")
    
    density_matrix = np.array(density_history).T # Transpor para [Preços (Y) x Tempo (X)]
    
    plt.figure(figsize=(14, 8))
    
    # Plot 1: Heatmap da Densidade de Probabilidade
    # Inverter o eixo Y para o menor preço ficar embaixo
    extent = [0, len(density_history), price_min, price_max]
    plt.imshow(density_matrix, aspect='auto', origin='lower', cmap='inferno', extent=extent, alpha=0.8)
    
    # Plot 2: Ação de Preço (Fechamentos)
    plt.plot(range(len(density_history)), df['close'].iloc[1:].values, color='cyan', linewidth=1.5, label='Ação do Preço Físico (GER40)')
    
    plt.title('Aethelgard Q-MATH: Equação de Schrödinger vs GER40 Cash (H2)', fontsize=14, fontweight='bold', color='white')
    plt.xlabel('Dimensão Temporal (Ticks/Candles)', color='lightgrey')
    plt.ylabel('Nível de Preço ($x$)', color='lightgrey')
    
    # Estilização "Dark Mode Neural"
    ax = plt.gca()
    ax.set_facecolor('#121212')
    plt.gcf().patch.set_facecolor('#121212')
    ax.tick_params(colors='lightgrey')
    
    cbar = plt.colorbar(label='Amplitude Probabilística $|\Psi(x,t)|^2$')
    cbar.ax.yaxis.label.set_color('lightgrey')
    cbar.ax.tick_params(colors='lightgrey')
    
    plt.legend(loc='upper left', facecolor='black', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "Schrodinger_Cloud_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"\n[SUCESSO] Renderização Quântica salva em: {output_path}")

if __name__ == "__main__":
    test_quantum_clouds()
