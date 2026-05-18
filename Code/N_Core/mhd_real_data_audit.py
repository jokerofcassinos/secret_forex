import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))

from plasma_market import PlasmaMarketTracker

def run_real_data_audit():
    print("NEXUS MHD AUDIT - Iniciando Simulação Contínua (Real Data)...")
    
    # 1. Geração de Série Temporal Realista (FBM com Momentum)
    N = 1000
    np.random.seed(42)
    returns = np.random.normal(0, 1, N)
    
    # Injetando tsunamis de liquidez (Trends)
    returns[100:200] += 0.5   # Bull Tsunami
    returns[400:550] -= 0.6   # Bear Tsunami
    returns[800:900] += 0.55  # Bull Tsunami
    
    price = np.zeros(N)
    price[0] = 24000.0 # GER40 base
    for i in range(1, N):
        price[i] = price[i-1] + returns[i] * 5.0
        
    # Volumes: Maior nas quedas fortes e subidas fortes
    volumes = np.abs(returns) * 500 + np.random.uniform(100, 300, N)
    
    # ATR (Ruído Térmico Dinâmico)
    atr_values = np.abs(returns) * 3.0 + 5.0

    # 2. Setup do Rastreador de Plasma
    tracker = PlasmaMarketTracker(grid_size=128)
    
    history = []
    
    print("Processando Fluido Magnético (1000 barras)...")
    for i in range(1, N):
        curr_candle = {'close': price[i], 'tick_volume': volumes[i]}
        prev_candle = {'close': price[i-1]}
        
        # Simulando as zonas ativas rastreando o preço atual (Holographic Horizon móvel)
        plasma_zones = {
            'top_level': price[i] + 50.0,
            'bottom_level': price[i] - 50.0,
            'top_density': 10.0,
            'bottom_density': 10.0,
            'atr': atr_values[i]
        }
        
        stability, signal, metrics = tracker.process_tick(curr_candle, prev_candle, plasma_zones, dt=0.01)
        state = tracker.get_state()
        
        if state:
            history.append({
                'price': price[i],
                'volume': volumes[i],
                'stability': stability,
                'signal': signal,
                'beta': metrics.get('beta', 1.0),
                'v_alfven': metrics.get('v_alfven', 0.0),
                'p_mag': metrics.get('p_mag', 0.0),
                'tension': metrics.get('tension', 0.0),
                'reconnection': state.magnetic_reconnection
            })
            
    df_audit = pd.DataFrame(history)
    
    # 4. Visualização de Singularidade
    plt.style.use('dark_background')
    fig, axes = plt.subplots(3, 1, figsize=(16, 20), gridspec_kw={'height_ratios': [1, 1, 1]})
    
    # Plot 1: Preço vs Campo Magnético (Volume) e Reconexões
    ax1 = axes[0]
    ax1.plot(df_audit.index, df_audit['price'], color='white', label='GER40 Synthetic Price (Fluid Velocity)', linewidth=1.5)
    
    ax1_vol = ax1.twinx()
    ax1_vol.fill_between(df_audit.index, df_audit['volume'], color='purple', alpha=0.2, label='Institutional Volume (B-Field)')
    
    recons = df_audit[df_audit['reconnection'] == True]
    if not recons.empty:
        ax1.scatter(recons.index, recons['price'], color='red', marker='x', s=120, label='Magnetic Reconnection (X-Point)', zorder=5)
    
    ax1.set_title("Aethelgard MHD Continuous Audit: Price-Fluid vs Volume-Magnetic Field", fontsize=14, color='yellow')
    ax1.legend(loc='upper left')
    ax1.grid(alpha=0.1)
    
    # Plot 2: Estabilidade e Plasma Beta
    ax2 = axes[1]
    ax2.plot(df_audit.index, df_audit['stability'], color='lime', label='Magnetic Stability (Entropy Inverted)', linewidth=1.2)
    ax2_beta = ax2.twinx()
    
    # Suaviza o Beta e aplica log para lidar com os spikes extremos (vistos na auditoria anterior)
    safe_beta = np.log1p(df_audit['beta'].replace([np.inf, -np.inf], np.nan).fillna(1.0))
    ax2_beta.plot(df_audit.index, safe_beta, color='orange', label='Log(Market Beta) - Thermal Overload', linestyle='-', alpha=0.8)
    
    ax2.set_title("MHD Stability & Log(Market Beta) Evolution", fontsize=14)
    ax2.legend(loc='upper left')
    ax2_beta.legend(loc='upper right')
    ax2.grid(alpha=0.1)
    
    # Plot 3: Velocidade de Alfvén e Tensão Magnética
    ax3 = axes[2]
    ax3.plot(df_audit.index, df_audit['v_alfven'], color='magenta', label='Alfven Velocity (Liquidity Wave Speed)')
    ax3_tens = ax3.twinx()
    ax3_tens.plot(df_audit.index, df_audit['tension'], color='cyan', label='Magnetic Tension (Lorentz Force Gradient)', alpha=0.5)
    
    ax3.set_title("Alfven Fluid Dynamics & Lorentz Stress", fontsize=14)
    ax3.legend(loc='upper left')
    ax3_tens.legend(loc='upper right')
    ax3.grid(alpha=0.1)
    
    plt.tight_layout()
    
    artifacts_dir = os.path.join(current_dir, '..', '..', 'artifacts')
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir)
        
    save_path = os.path.join(artifacts_dir, 'MHD_RealData_Audit.png')
    plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"✅ AUDIT COMPLETE. Visualização salva em: {save_path}")
    print(f"💥 X-Points (Reconexões) Detectados: {len(recons)}")

if __name__ == "__main__":
    run_real_data_audit()
