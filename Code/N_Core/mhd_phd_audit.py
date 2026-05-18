import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Garante que o diretório N_Core e os binários C++ estejam no path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))

from plasma_market import PlasmaMarketTracker

def run_mhd_audit():
    print("NEXUS MHD AUDIT - Iniciando Simulação de Campo Magnético...")
    
    # 1. Setup do Rastreador de Plasma
    tracker = PlasmaMarketTracker(grid_size=128)
    
    # 2. Geração de Dados Sintéticos (Regime de Sweep e Reconexão)
    # Simula um sweep de fundo seguido de reversão violenta
    n_ticks = 200
    prices = np.linspace(100, 95, 100).tolist() + np.linspace(95, 105, 100).tolist()
    volumes = [100 + i*5 for i in range(100)] + [500 - i*4 for i in range(100)]
    
    # Zonas de Plasma
    plasma_zones = {
        'top_level': 104.0,
        'bottom_level': 96.0,
        'top_density': 10.0,
        'bottom_density': 12.0,
        'atr': 1.5
    }
    
    history = []
    
    # 3. Execução da Simulação
    for i in range(1, n_ticks):
        curr_candle = {'close': prices[i], 'tick_volume': volumes[i]}
        prev_candle = {'close': prices[i-1]}
        
        stability, signal, metrics = tracker.process_tick(curr_candle, prev_candle, plasma_zones, dt=0.01)
        
        state = tracker.get_state()
        if state:
            history.append({
                'price': prices[i],
                'volume': volumes[i],
                'stability': stability,
                'signal': signal,
                'beta': metrics['beta'],
                'v_alfven': metrics['v_alfven'],
                'p_mag': metrics['p_mag'],
                'tension': metrics['tension'],
                'reconnection': state.magnetic_reconnection,
                'b_grid': state.b_grid
            })
            
    df_audit = pd.DataFrame(history)
    
    # 4. Visualização de Singularidade
    fig, axes = plt.subplots(3, 1, figsize=(14, 18), gridspec_kw={'height_ratios': [1, 1, 1]})
    plt.style.use('dark_background')
    
    # Plot 1: Preço vs Campo Magnético (Volume) e Sinais
    ax1 = axes[0]
    ax1.plot(df_audit.index, df_audit['price'], color='cyan', label='Price (Fluid Velocity)', linewidth=2)
    ax1_vol = ax1.twinx()
    ax1_vol.fill_between(df_audit.index, df_audit['volume'], color='purple', alpha=0.3, label='Volume (Magnetic Field)')
    
    # Destaca Reconexão Magnética
    recons = df_audit[df_audit['reconnection'] == True]
    if not recons.empty:
        ax1.scatter(recons.index, recons['price'], color='red', marker='x', s=100, label='Magnetic Reconnection (X-Point)')
    
    ax1.set_title("Aethelgard MHD Audit: Price-Fluid vs Volume-Magnetic Interaction", fontsize=16, color='yellow')
    ax1.legend(loc='upper left')
    ax1.grid(alpha=0.2)
    
    # Plot 2: Estabilidade e Plasma Beta
    ax2 = axes[1]
    ax2.plot(df_audit.index, df_audit['stability'], color='lime', label='Magnetic Stability Score', linewidth=2)
    ax2_beta = ax2.twinx()
    ax2_beta.plot(df_audit.index, df_audit['beta'], color='orange', label='Market Beta (Thermal/Magnetic)', linestyle='--')
    
    # Linhas de Regime
    ax2_beta.axhline(y=1.0, color='red', linestyle=':', alpha=0.5, label='Beta Threshold (Turbulence)')
    
    ax2.set_title("MHD Stability & Market Beta Evolution", fontsize=14)
    ax2.legend(loc='upper left')
    ax2_beta.legend(loc='upper right')
    ax2.grid(alpha=0.2)
    
    # Plot 3: Velocidade de Alfvén e Tensão Magnética
    ax3 = axes[2]
    ax3.plot(df_audit.index, df_audit['v_alfven'], color='magenta', label='Alfven Velocity (Liquidity Waves)')
    ax3_tens = ax3.twinx()
    ax3_tens.plot(df_audit.index, df_audit['tension'], color='white', label='Magnetic Tension (Lorentz Force)', alpha=0.6)
    
    ax3.set_title("Liquidity Wave Propagation (Alfven) & Lorentz Stress", fontsize=14)
    ax3.legend(loc='upper left')
    ax3_tens.legend(loc='upper right')
    ax3.grid(alpha=0.2)
    
    plt.tight_layout()
    
    artifacts_dir = os.path.join(current_dir, '..', '..', 'artifacts')
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir)
        
    save_path = os.path.join(artifacts_dir, 'MHD_Magnetic_Field_Audit.png')
    plt.savefig(save_path)
    print(f"AUDIT COMPLETE. Visualização salva em: {save_path}")
    
    # Resumo Executivo
    print("\n[RESULTADOS DA SIMULAÇÃO]")
    print(f"Estabilidade Média: {df_audit['stability'].mean():.2f}")
    print(f"Ocorrências de Reconexão: {df_audit['reconnection'].sum()}")
    print(f"Beta de Mercado Médio: {df_audit['beta'].mean():.4f}")
    print(f"Velocidade de Alfvén Máxima: {df_audit['v_alfven'].max():.4f}")

if __name__ == "__main__":
    run_mhd_audit()
