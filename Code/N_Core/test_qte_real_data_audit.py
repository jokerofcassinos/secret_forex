import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import sys
import os

# Configuração de Caminhos
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

from Code.N_Core.quantum_tunneling import QuantumTunnelingNode

def run_impeccable_qte_audit():
    print("[QTE] Gerando Visualização Impecável de Tunelamento (Real Data)...")
    
    if not mt5.initialize():
        return
        
    target = "GER40.cash"
    rates = mt5.copy_rates_from_pos(target, mt5.TIMEFRAME_M1, 0, 500)
    mt5.shutdown()
    
    if rates is None: return

    df = pd.DataFrame(rates)
    node = QuantumTunnelingNode()
    
    # Prepara Barreira de Potencial Real (Volume Profile)
    price_min = df['low'].min()
    price_max = df['high'].max()
    bins = np.linspace(price_min, price_max, 100)
    v_density, _ = np.histogram(df['close'], bins=bins, weights=df['tick_volume'])
    v_density = v_density / (v_density.max() + 1e-9)

    tunneling_history = []
    energy_history = []
    
    # Simulação da evolução
    for i in range(50, len(df)):
        curr_p = df['close'].iloc[i]
        # Energia baseada no Momentum local
        mom = abs(curr_p - df['close'].iloc[i-10]) / (df['close'].iloc[i-10] + 1e-9)
        energy = mom * 10.0 # Escalado para visualização
        
        p_idx = np.searchsorted(bins, curr_p)
        local_v = v_density[max(0, p_idx-5):min(len(v_density), p_idx+5)]
        
        t_prob = node.engine.calculate_tunneling_probability(curr_p, energy, local_v)
        tunneling_history.append(t_prob)
        energy_history.append(energy)
        
    tunneling_history = [0]*50 + tunneling_history
    energy_history = [0]*50 + energy_history

    # --- SETUP VISUAL IMPECÁVEL ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 12), facecolor='#020202')
    gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])
    
    ax_main = fig.add_subplot(gs[0])
    ax_wave = fig.add_subplot(gs[1])
    ax_prob = fig.add_subplot(gs[2])
    
    # 1. MAIN CHART: LIQUIDITY MANIFOLD
    # Heatmap de fundo
    for i in range(len(bins)-1):
        density = v_density[i]
        if density > 0.05:
            ax_main.axhspan(bins[i], bins[i+1], color='#ff003c', alpha=density*0.25, zorder=1)
            
    ax_main.plot(df.index, df['close'], color='white', linewidth=1.5, zorder=10, label='GER40 Price Flow')
    
    # Destaque de Tunelamento (Hold for Breakout)
    tunneling_mask = np.array(tunneling_history) >= 0.85
    ax_main.scatter(df.index[tunneling_mask], df['close'][tunneling_mask], 
                   color='cyan', s=30, alpha=0.6, label='Quantum Tunneling (Breakout Momentum)', zorder=11)
    
    ax_main.set_title("NEXUS QTE :: QUANTUM TUNNELING MANIFOLD (WKB PROJECTION)", color='cyan', fontsize=16, loc='left', pad=15)
    ax_main.legend(facecolor='#0a0a0a', edgecolor='#333333')
    ax_main.grid(alpha=0.05)

    # 2. WKB WAVEFUNCTION (Onda atravessando a Barreira)
    # Visualizamos a "Energia" vs "Barreira" no ponto mais recente
    last_idx = np.searchsorted(bins, df['close'].iloc[-1])
    local_barrier = v_density[max(0, last_idx-10):min(len(v_density), last_idx+10)]
    x_bar = np.linspace(-5, 5, len(local_barrier))
    
    ax_wave.fill_between(x_bar, local_barrier, color='red', alpha=0.4, label='Liquidity Barrier V(x)')
    # Simula a função de onda decaindo
    wave_x = np.linspace(-5, 5, 100)
    wave_y = 0.5 * np.exp(-wave_x) * np.sin(wave_x*10) # Simbolismo visual WKB
    ax_wave.plot(wave_x, wave_y + energy_history[-1], color='cyan', linewidth=2, label='Price Wavefunction (Psi)')
    
    ax_wave.set_title("WKB WAVEFUNCTION DECAY (INSTANTANEOUS STATE)", color='white', fontsize=12)
    ax_wave.set_facecolor('#050505')
    ax_wave.legend()

    # 3. TRANSMISSION COEFFICIENT (T)
    cmap_prob = LinearSegmentedColormap.from_list('prob', ['#222222', '#00ffb4'])
    ax_prob.plot(df.index, tunneling_history, color='#00ffb4', linewidth=2, label='Tunneling Probability (T)')
    ax_prob.fill_between(df.index, tunneling_history, 0, color='#00ffb4', alpha=0.15)
    ax_prob.axhline(0.85, color='white', linestyle=':', alpha=0.5, label='Tunneling Threshold')
    
    ax_prob.set_title("QUANTUM TRANSMISSION FLOW (HOLD VS EXIT ADVICE)", color='lime', fontsize=12)
    ax_prob.set_ylim(-0.05, 1.05)
    ax_prob.grid(alpha=0.05)

    for ax in [ax_main, ax_wave, ax_prob]:
        ax.set_facecolor('#020202')
        ax.tick_params(colors='#888888', labelsize=8)
        for spine in ax.spines.values(): spine.set_color('#222222')

    plt.tight_layout()
    save_path = "Code/N_Core/QTE_RealData_Impeccable.png"
    plt.savefig(save_path, dpi=250, facecolor='#020202')
    print(f"SUCCESS: Auditoria Impecável QTE salva em: {save_path}")

if __name__ == "__main__":
    run_impeccable_qte_audit()
