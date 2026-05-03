import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Ensure we can import the agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Code.N_Core.quantum_clouds import QuantumCloudTracker

def test_sec_singularity():
    print("Iniciando simulação visual: Singularidade Estocástica (SEC) - Timeframe H2")
    
    data_path = os.path.join("Data", "Historical", "BTCUSD_H1.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Usando dados sintéticos.")
        dates = pd.date_range('2023-01-01', periods=300, freq='1h')
        # Simula um "Tsunami" direcional forte
        prices = 18000 + np.cumsum(np.random.randn(300) * 10)
        prices[150:200] += np.linspace(0, 1000, 50) # Expansão violenta
        highs = prices + 20; lows = prices - 20; volumes = np.random.randint(2000, 8000, 300)
        df = pd.DataFrame({'time': dates, 'open': prices, 'high': highs, 'low': lows, 'close': prices, 'tick_volume': volumes})
    else:
        print(f"Carregando {data_path}...")
        df = pd.read_parquet(data_path)
        df = df.tail(300).reset_index(drop=True)
    
    price_min = df['low'].min() - 200
    price_max = df['high'].max() + 200
    
    tracker = QuantumCloudTracker(price_min=price_min, price_max=price_max, bins=500)
    
    density_history = []
    sec_history = [] # Força da singularidade e flag de colapso
    
    print("Processando Malha de Schwarzschild em C++...")
    tracker.initialize_wave(df['close'].iloc[0], sigma=(tracker.dx * 15))
    
    for i in range(1, len(df)):
        window = max(0, i - 30)
        df_slice = df.iloc[window:i+1]
        
        density = tracker.step(df_slice, dt=1.0)
        metrics = tracker.get_singularity_metrics()
        
        density_history.append(np.array(density))
        sec_history.append(metrics)
        
    print("Renderizando Horizonte de Eventos...")
    
    density_matrix = np.array(density_history).T
    
    plt.figure(figsize=(16, 10))
    
    # Plot 1: Heatmap da Nuvem de Schrödinger
    extent = [0, len(density_history), price_min, price_max]
    plt.imshow(density_matrix, aspect='auto', origin='lower', cmap='magma', extent=extent, alpha=0.7)
    
    # Plot 2: Ação de Preço
    plt.plot(range(len(density_history)), df['close'].iloc[1:].values, color='cyan', linewidth=1.2, label='Preço Físico')
    
    # Plot 3: Zonas de Colapso SEC (Horizonte de Eventos)
    for i, m in enumerate(sec_history):
        if m['is_collapsed']:
            peak_p = m['peak_price']
            rs = m['schwarzschild_radius'] * tracker.dx
            # Desenha o Horizonte de Eventos (Raio de Schwarzschild financeiro)
            plt.fill_between([i, i+1], peak_p - rs, peak_p + rs, color='red', alpha=0.3)
            if i % 20 == 0:
                plt.scatter(i, peak_p, marker='o', color='white', s=20, edgecolors='black', label='Singularidade' if i==0 else "")

    plt.title('NEXUS AGI-5 :: Singularidade Estocástica & Colapso de Horizonte (SEC)', fontsize=16, fontweight='bold', color='white')
    plt.xlabel('Dimensão Temporal (Ticks/H2)', color='white')
    plt.ylabel('Preço (Raio de Curvatura)', color='white')
    
    ax = plt.gca()
    ax.set_facecolor('#050505')
    plt.gcf().patch.set_facecolor('#050505')
    ax.tick_params(colors='white')
    
    cbar = plt.colorbar(label='Densidade de Massa Institucional')
    cbar.ax.yaxis.label.set_color('white')
    cbar.ax.tick_params(colors='white')
    
    # Adicionar legenda customizada
    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='cyan', lw=2),
                    Line2D([0], [0], color='red', alpha=0.4, lw=6),
                    Line2D([0], [0], marker='o', color='w', markerfacecolor='w', markersize=5)]
    plt.legend(custom_lines, ['Preço', 'Horizonte de Eventos (TP=0)', 'Singularidade'], loc='upper left', facecolor='black', labelcolor='white')
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "Schrodinger_SEC_Singularity.png")
    plt.savefig(output_path, dpi=300, facecolor='#050505')
    print(f"\n[SUCESSO] Renderização SEC salva em: {output_path}")

if __name__ == "__main__":
    test_sec_singularity()
