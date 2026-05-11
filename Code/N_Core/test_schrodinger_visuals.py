import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Definir Raiz do Projeto (ASI v3.2 Mapping)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(ROOT_DIR, 'Code')) # Para imports internos se necessário

from N_Core.quantum_clouds import QuantumCloudTracker

def test_quantum_clouds():
    print("Iniciando simulação visual: Nuvens de Probabilidade de Schrödinger - Timeframe H2")
    
    data_path = os.path.join(ROOT_DIR, "Data", "Historical", "BTCUSD_H2.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Tentando H1 ou sintético.")
        data_path_h1 = os.path.join(ROOT_DIR, "Data", "Historical", "BTCUSD_H1.parquet")
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
        df = df.tail(200).reset_index(drop=True)
    
    # 1. Definir Referencial Global de Preço (v24.1)
    global_price_min = df['low'].min() - 150
    global_price_max = df['high'].max() + 150
    global_bins = 800
    global_y_axis = np.linspace(global_price_min, global_price_max, global_bins)
    
    print(f"Referencial Global: {global_price_min:.2f} a {global_price_max:.2f}")
    
    tracker = QuantumCloudTracker(price_min=df['close'].iloc[0]-400, price_max=df['close'].iloc[0]+400, bins=500)
    
    if not tracker.is_active:
        print("Erro: Motor C++ não carregado. Verifique a compilação.")
        return

    global_density_history = []
    global_delta_history = [] # v35.2: Histórico de Polaridade
    
    print("Processando fluxo de ticks através da Malha Quântica C++...")
    tracker.initialize_wave(df['close'].iloc[0], sigma=(tracker.dx * 65))
    
    for i in range(1, len(df)):
        window = max(0, i - 20)
        df_slice = df.iloc[window:i+1]
        
        res = tracker.step(df_slice, dt=1.2, steps=15)
        
        if res is not None:
            density, reset = res
            
            local_y_axis = np.linspace(tracker.price_min, tracker.price_max, tracker.bins)
            interpolated_density = np.interp(global_y_axis, local_y_axis, np.nan_to_num(density), left=0, right=0)
            
            # v35.2: Interpolação do Campo de Delta
            interpolated_delta = np.interp(global_y_axis, local_y_axis, np.nan_to_num(tracker.delta_field), left=0, right=0)
            
            global_density_history.append(interpolated_density)
            global_delta_history.append(interpolated_delta)
        
    print("Renderizando Espectrografia de Polaridade (v35.3)...")
    
    upsample_factor = 4
    num_steps_orig = len(global_density_history)
    num_steps_up = num_steps_orig * upsample_factor
    global_bins = len(global_y_axis)
    
    up_matrix_buy = np.zeros((global_bins, num_steps_up))
    up_matrix_sell = np.zeros((global_bins, num_steps_up))
    
    # Derivação de Preço para Translação Geométrica
    prices_array = df['close'].iloc[1:num_steps_orig+1].values
    dx_global = (global_price_max - global_price_min) / global_bins
    
    for t in range(num_steps_orig - 1):
        d1 = global_density_history[t]
        d2 = global_density_history[t+1]
        dl1 = global_delta_history[t]
        dl2 = global_delta_history[t+1]
        
        p1 = prices_array[t]
        p2 = prices_array[t+1]
        dp_bins = int((p2 - p1) / dx_global)
        
        for sub in range(upsample_factor):
            frac = sub / upsample_factor
            idx_up = t * upsample_factor + sub
            shift_frac = int(dp_bins * frac)
            
            # Blend de Densidade e Delta
            d_mid = (1.0 - frac) * np.roll(d1, shift_frac) + frac * d2
            dl_mid = (1.0 - frac) * np.roll(dl1, shift_frac) + frac * dl2
            
            # Separação por Polaridade
            up_matrix_buy[:, idx_up] = d_mid * (dl_mid > 0) * np.abs(dl_mid)
            up_matrix_sell[:, idx_up] = d_mid * (dl_mid < 0) * np.abs(dl_mid)

    # Suavização Temporal e Espacial v37.2 (Lush Nebula - Manual Kernel)
    alpha_ema = 0.6
    
    def smooth_2d(matrix, passes=2):
        temp = matrix.copy()
        for _ in range(passes):
            # Média com vizinhos (acima e abaixo) para efeito de névoa vertical
            temp[1:-1, :] = (temp[:-2, :] + temp[1:-1, :] + temp[2:, :]) / 3.0
            # Média com vizinhos (esquerda e direita) para fluidez temporal
            temp[:, 1:-1] = (temp[:, :-2] + temp[:, 1:-1] + temp[:, 2:]) / 3.0
        return temp

    print("Aplicando Filtro de Névoa 2D (v37.2)...")
    up_matrix_buy = smooth_2d(up_matrix_buy, passes=3)
    up_matrix_sell = smooth_2d(up_matrix_sell, passes=3)

    for t in range(1, num_steps_up):
        up_matrix_buy[:, t] = alpha_ema * up_matrix_buy[:, t] + (1 - alpha_ema) * up_matrix_buy[:, t-1]
        up_matrix_sell[:, t] = alpha_ema * up_matrix_sell[:, t] + (1 - alpha_ema) * up_matrix_sell[:, t-1]
    
    # Normalização UNIFICADA e Gamma de Névoa (v37.2)
    max_val = max(np.max(up_matrix_buy), np.max(up_matrix_sell), 1e-9)
    up_matrix_buy = np.power(up_matrix_buy / max_val, 0.4) 
    up_matrix_sell = np.power(up_matrix_sell / max_val, 0.4)

    # Custom Colormaps: Lush Neon with Smooth Alpha (v37.2)
    from matplotlib.colors import LinearSegmentedColormap
    # Transparência graduada para efeito de névoa
    cmap_buy = LinearSegmentedColormap.from_list('lush_buy', [(0,0,0,0), (0,0.4,0.8,0.3), (0,1,1,1)], N=256)
    cmap_sell = LinearSegmentedColormap.from_list('lush_sell', [(0,0,0,0), (0.6,0,0.8,0.3), (1,0,1,1)], N=256)

    plt.figure(figsize=(16, 9), facecolor='black')
    ax = plt.gca()
    ax.set_facecolor('black')
    
    extent = [0, num_steps_orig, global_price_min, global_price_max]
    
    # Plot layers com interpolação bicúbica para suavidade extrema
    plt.imshow(up_matrix_buy, aspect='auto', origin='lower', cmap=cmap_buy, 
               extent=extent, alpha=0.9, interpolation='bicubic', vmin=1e-12, vmax=0.85)
    plt.imshow(up_matrix_sell, aspect='auto', origin='lower', cmap=cmap_sell, 
               extent=extent, alpha=0.9, interpolation='bicubic', vmin=1e-12, vmax=0.85)
    
    plt.plot(np.arange(num_steps_orig), df['close'].iloc[1:num_steps_orig+1].values, 
             color='white', linewidth=1.2, alpha=0.6, label='Fluxo do Preço (GER40)')
    
    plt.title('NEXUS-QUANT v35.3: Espectrografia de Delta & Burn Rate (Institutional Flow)', 
              fontsize=16, fontweight='bold', color='white', pad=20)
    plt.xlabel('Dimensão Temporal (Ticks/Candles)', color='white')
    plt.ylabel('Nível de Preço (x)', color='white')
    ax.tick_params(colors='white')
    
    plt.grid(color='white', alpha=0.05)
    plt.legend(facecolor='black', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    
    # Garantir existência do diretório de saída (ASI v3.2 Safety)
    output_dir = os.path.join(ROOT_DIR, "Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    output_path = os.path.join(output_dir, "Schrodinger_Cloud_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='black')
    print(f"\n[SUCESSO] Renderização de Polaridade em: {output_path}")

if __name__ == "__main__":
    test_quantum_clouds()
