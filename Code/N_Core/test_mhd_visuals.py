import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Code.N_Core.plasma_market import PlasmaMarketTracker

def test_mhd_zpinch():
    print("Iniciando simulação visual: MHD Plasma Market (Z-Pinch) - Timeframe H2")
    
    data_path = os.path.join("Data", "Historical", "BTCUSD_H2.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Tentando H1 ou sintético.")
        # Se H2 não existir, tenta H1 para compor ou falha pro sintético (já que a ponte mt5 só salva H1 e H4 por padrão)
        data_path_h1 = os.path.join("Data", "Historical", "BTCUSD_H1.parquet")
        if os.path.exists(data_path_h1):
             print(f"Carregando {data_path_h1} e re-amostrando para H2...")
             df_h1 = pd.read_parquet(data_path_h1)
             # Simplificando a re-amostragem para teste visual
             df = df_h1.iloc[::2].reset_index(drop=True)
             df = df.tail(1000).reset_index(drop=True)
        else:
             print("Usando dados sintéticos (H2).")
             dates = pd.date_range('2023-01-01', periods=500, freq='2h')
             prices = 18000 + np.cumsum(np.random.randn(500) * 15)
             # Forçar um stop hunt massivo de H2 no final
             prices[-20:] = prices[-20] + np.arange(20) * 8
             prices[-1] -= 50
             
             highs = prices + np.random.rand(500) * 10
             lows = prices - np.random.rand(500) * 10
             volumes = np.random.randint(500, 5000, 500)
             df = pd.DataFrame({'time': dates, 'open': prices, 'high': highs, 'low': lows, 'close': prices, 'tick_volume': volumes})
    else:
        print(f"Carregando {data_path}...")
        df = pd.read_parquet(data_path)
        df = df.tail(1000).reset_index(drop=True)
        
    tracker = PlasmaMarketTracker()
    
    if not tracker.is_active:
        print("Erro: Motor C++ MHD não carregado.")
        return

    # Histórico para plotagem
    z_indexes = []
    z_pinch_signals = []
    
    # Escaneia a zona de plasma macro
    plasma_zones = tracker.scan_for_plasma_zones(df, lookback=500)
    
    print(f"Zonas de Plasma Detectadas:")
    print(f"  - Topo (Resistance): {plasma_zones['top_level']:.2f} (Densidade: {plasma_zones['top_density']})")
    print(f"  - Fundo (Support): {plasma_zones['bottom_level']:.2f} (Densidade: {plasma_zones['bottom_density']})")
    
    for i in range(1, len(df)):
        curr_c = df.iloc[i]
        prev_c = df.iloc[i-1]
        
        z_idx, zone_type = tracker.process_tick(curr_c, prev_c, plasma_zones)
        z_indexes.append(z_idx)
        
        if z_idx > 90.0:
            z_pinch_signals.append((i, curr_c['close'], zone_type))
            
    # --- RENDERIZAÇÃO ---
    print("Renderizando Gráfico de Compressão Magnética...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot 1: Preço e Zonas de Plasma
    ax1.plot(df.index[1:], df['close'].iloc[1:], color='cyan', linewidth=1)
    
    # Desenhar as zonas de plasma
    ax1.axhline(plasma_zones['top_level'], color='red', linestyle='--', alpha=0.5, label='Plasma Superior (Stops Shorts)')
    ax1.axhline(plasma_zones['bottom_level'], color='lime', linestyle='--', alpha=0.5, label='Plasma Inferior (Stops Longs)')
    
    # Marcar os Sinais Z-Pinch
    for idx, price, ztype in z_pinch_signals:
        color = 'yellow' if ztype == "BOTTOM_SWEEP" else 'magenta'
        marker = '^' if ztype == "BOTTOM_SWEEP" else 'v'
        ax1.scatter(idx, price, color=color, marker=marker, s=150, zorder=5, edgecolors='black')
        
    ax1.set_title('Aethelgard Q-MATH: Efeito Z-Pinch (Stop Hunt Colapso)', color='white')
    ax1.legend(facecolor='black', labelcolor='white')
    
    # Plot 2: Índice de Compressão Z-Pinch
    ax2.plot(df.index[1:], z_indexes, color='orange', linewidth=1.5, label='Z-Index (Compressão Magnética)')
    ax2.axhline(90, color='red', linestyle=':', label='Limiar de Ruptura Crítica (90%)')
    ax2.fill_between(df.index[1:], z_indexes, alpha=0.3, color='orange')
    ax2.set_ylabel('Z-Index', color='lightgrey')
    ax2.legend(facecolor='black', labelcolor='white')
    
    # Estilização
    for ax in [ax1, ax2]:
        ax.set_facecolor('#121212')
        ax.tick_params(colors='lightgrey')
    fig.patch.set_facecolor('#121212')
    plt.tight_layout()
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "Plasma_ZPinch_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"[SUCESSO] Renderização Z-Pinch salva em: {output_path}")

if __name__ == "__main__":
    test_mhd_zpinch()
