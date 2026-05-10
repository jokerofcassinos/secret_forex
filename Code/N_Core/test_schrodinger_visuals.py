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
    
    data_path = os.path.join("Data", "Historical", "BTCUSD_H2.parquet")
    if not os.path.exists(data_path):
        print(f"Erro: Base de dados {data_path} não encontrada. Tentando H1 ou sintético.")
        data_path_h1 = os.path.join("Data", "Historical", "BTCUSD_H1.parquet")
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
    
    print("Processando fluxo de ticks através da Malha Quântica C++...")
    tracker.initialize_wave(df['close'].iloc[0], sigma=(tracker.dx * 65))
    
    last_density = None
    for i in range(1, len(df)):
        window = max(0, i - 20)
        df_slice = df.iloc[window:i+1]
        
        res = tracker.step(df_slice, dt=1.2, steps=15)
        
        if res is not None:
            density, reset = res
            
            # v25.4: TEMPORAL BLOOM (Persistência Quântica)
            if last_density is not None:
                density = 0.6 * density + 0.4 * last_density
                density /= (np.sum(density) + 1e-9)
            last_density = density

            # Telemetria v24.1
            if i % 50 == 0:
                print(f"Tick {i} | Density Max: {np.max(density):.6f} | Price: {df['close'].iloc[i]:.2f}")
            
            local_y_axis = np.linspace(tracker.price_min, tracker.price_max, tracker.bins)
            interpolated_density = np.interp(global_y_axis, local_y_axis, np.nan_to_num(density), left=0, right=0)
            global_density_history.append(interpolated_density)
        
    print("Renderizando Espectrografia de Atração (v24.1)...")
    
    # v25.2: INTERPOLAÇÃO SUB-CANDLE (Upsampling Temporal para continuidade total)
    upsample_factor = 4
    num_steps_orig = len(global_density_history)
    num_steps_up = num_steps_orig * upsample_factor
    
    upsampled_matrix = np.zeros((global_bins, num_steps_up))
    
    print(f"Upsampling Temporal (4x) para Fluidez Total: {num_steps_up} colunas...")
    
    for t in range(num_steps_orig - 1):
        d1 = global_density_history[t]
        d2 = global_density_history[t+1]
        
        for sub in range(upsample_factor):
            frac = sub / upsample_factor
            idx_up = t * upsample_factor + sub
            upsampled_matrix[:, idx_up] = (1.0 - frac) * d1 + frac * d2

    # Suavização Temporal EMA no grid upsampled
    smoothed_matrix = np.zeros_like(upsampled_matrix)
    alpha = 0.20 # v25.3: Persistência extrema para Campo Unificado
    for t in range(upsampled_matrix.shape[1]):
        if t == 0: smoothed_matrix[:, t] = upsampled_matrix[:, t]
        else: smoothed_matrix[:, t] = alpha * upsampled_matrix[:, t] + (1 - alpha) * smoothed_matrix[:, t-1]
    
    # v25.3.1: MANUAL TEMPORAL SMEAR (Bypass Scipy)
    # Aplicamos uma convolução gaussiana 1D em cada linha (preço) para conectar o tempo
    kernel = np.array([0.05, 0.2, 0.5, 0.2, 0.05])
    final_matrix = np.zeros_like(smoothed_matrix)
    
    print("Aplicando Smear Temporal via Convolução Quântica...")
    for i in range(smoothed_matrix.shape[0]):
        final_matrix[i, :] = np.convolve(smoothed_matrix[i, :], kernel, mode='same')

    plt.figure(figsize=(14, 8))
    
    extent = [0, num_steps_orig, global_price_min, global_price_max]
    vmax_val = np.percentile(final_matrix, 99.5) if np.max(final_matrix) > 0 else 0.2
    
    plt.imshow(final_matrix, aspect='auto', origin='lower', cmap='inferno', 
               extent=extent, alpha=0.9, interpolation='gaussian', vmin=0, vmax=vmax_val)
    
    # Ajusta o eixo x do preço para o grid original
    plt.plot(np.arange(num_steps_orig), df['close'].iloc[1:num_steps_orig+1].values, color='cyan', linewidth=1.5, label='Ação do Preço Físico (GER40)')
    
    plt.title('Aethelgard Q-MATH: Superfluidez Institucional v25.4 (Atração de Campo Fluido)', fontsize=14, fontweight='bold', color='white')
    plt.xlabel('Dimensão Temporal (Ticks/Candles)', color='lightgrey')
    plt.ylabel('Nível de Preço ($x$)', color='lightgrey')
    
    ax = plt.gca()
    ax.set_facecolor('#121212')
    plt.gcf().patch.set_facecolor('#121212')
    ax.tick_params(colors='lightgrey')
    
    cbar = plt.colorbar(label=r'Amplitude Probabilística $|\Psi(x,t)|^2$')
    cbar.ax.yaxis.label.set_color('lightgrey')
    cbar.ax.tick_params(colors='lightgrey')
    
    plt.legend(loc='upper left', facecolor='black', edgecolor='white', labelcolor='white')
    plt.tight_layout()
    
    output_path = os.path.join("Docs", "05_Estrutura_Corporativa", "Setores", "Q_MATH", "Schrodinger_Cloud_Render.png")
    plt.savefig(output_path, dpi=300, facecolor='#121212')
    print(f"\n[SUCESSO] Renderização de Atração em: {output_path}")

if __name__ == "__main__":
    test_quantum_clouds()
