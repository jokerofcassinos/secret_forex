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

from Code.N_Core.quantum_oscillator import QuantumOscillatorNode

def run_impeccable_qho_audit():
    print("[QHO] Gerando Visualização Impecável (Real Data)...")
    
    if not mt5.initialize():
        return
        
    target = "GER40.cash"
    rates = mt5.copy_rates_from_pos(target, mt5.TIMEFRAME_M1, 0, 600)
    mt5.shutdown()
    
    if rates is None: return

    df = pd.DataFrame(rates)
    node = QuantumOscillatorNode()
    
    results = []
    for i in range(200, len(df)):
        window_df = df.iloc[:i+1]
        results.append(node.calculate_quantum_state(window_df))
        
    # Preenchimento inicial para manter o tamanho do array
    padding = [results[0]] * 200
    full_results = padding + results
    
    n_levels = np.array([r['n'] for r in full_results])
    stabilities = np.array([r['stability'] for r in full_results])
    ifv_history = np.array([r['ifv'] for r in full_results])
    z_scores = np.array([r['z_score'] if 'z_score' in r else 0 for r in full_results])
    
    # --- SETUP VISUAL IMPECÁVEL ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 12), facecolor='#020202')
    gs = fig.add_gridspec(3, 2, width_ratios=[3, 1], height_ratios=[3, 1, 1])
    
    ax_main = fig.add_subplot(gs[0, 0])
    ax_phase = fig.add_subplot(gs[0, 1])
    ax_energy = fig.add_subplot(gs[1, :])
    ax_stab = fig.add_subplot(gs[2, :])
    
    # 1. MAIN CHART: PRICE MANIFOLD & ENERGY SHELLS
    ax_main.plot(df.index, df['close'], color='white', linewidth=1.2, alpha=0.9, label='Price Flow', zorder=10)
    ax_main.plot(df.index, ifv_history, color='cyan', linestyle='--', linewidth=1, alpha=0.6, label='Inst. Fair Value (IFV)')
    
    # Desenha as "Cascas de Energia" (Energy Shells)
    # n=1, n=3, n=5 (Desvios Quânticos)
    std_avg = (df['close'] - ifv_history).std()
    for n in [1, 2, 3, 4, 5]:
        width = np.sqrt(n) * std_avg
        ax_main.fill_between(df.index, ifv_history - width, ifv_history + width, 
                            color='cyan', alpha=0.03, zorder=1)
        if n == 5: # Fronteira de Exaustão
             ax_main.plot(df.index, ifv_history + width, color='red', alpha=0.15, linestyle=':', linewidth=0.8)
             ax_main.plot(df.index, ifv_history - width, color='red', alpha=0.15, linestyle=':', linewidth=0.8)

    # Destaque de Exaustão Crítica
    exhaustion_mask = n_levels >= 5
    ax_main.scatter(df.index[exhaustion_mask], df['close'][exhaustion_mask], 
                   color='red', s=15, alpha=0.5, label='Quantum Exhaustion (n>=5)', zorder=11)
    
    ax_main.set_title("NEXUS QHO :: QUANTIZED FAIR VALUE MANIFOLD", color='cyan', fontsize=16, loc='left', pad=15)
    ax_main.legend(facecolor='#0a0a0a', edgecolor='#333333')
    ax_main.grid(alpha=0.05)

    # 2. PHASE SPACE (Órbita Harmônica)
    # Preço vs Velocidade (Momentum)
    momentum = pd.Series(df['close']).diff(5).fillna(0).values
    ax_phase.plot(z_scores, momentum, color='lime', alpha=0.3, linewidth=0.8)
    ax_phase.scatter(z_scores[-1], momentum[-1], color='cyan', s=50, edgecolors='white', label='Current State')
    ax_phase.axhline(0, color='white', alpha=0.2)
    ax_phase.axvline(0, color='white', alpha=0.2)
    ax_phase.set_title("PHASE SPACE ORBIT", color='white', fontsize=12)
    ax_phase.set_xlabel("Z-Score (Potential)")
    ax_phase.set_ylabel("Momentum (Kinetic)")
    
    # 3. ENERGY LEVEL (n) - Degrau Quantizado
    ax_energy.step(df.index, n_levels, where='post', color='orange', linewidth=1.5, label='Quantized Energy Level (n)')
    ax_energy.fill_between(df.index, n_levels, step='post', color='orange', alpha=0.1)
    ax_energy.set_ylim(-0.5, 12)
    ax_energy.set_title("STATIONARY ENERGY STATES (n)", color='orange', fontsize=12)
    ax_energy.grid(alpha=0.05)

    # 4. STABILITY FLOW
    cmap_stab = LinearSegmentedColormap.from_list('stab', ['#ff3232', '#ffc800', '#00ffb4'])
    points = np.array([df.index, stabilities]).T.reshape(-1, 1, 2)
    from matplotlib.collections import LineCollection
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=cmap_stab, linewidth=3)
    lc.set_array(stabilities)
    ax_stab.add_collection(lc)
    ax_stab.set_xlim(df.index.min(), df.index.max())
    ax_stab.set_ylim(-0.1, 1.1)
    ax_stab.set_title("QUANTUM STABILITY SCORE (WAVEFUNCTION FIDELITY)", color='lime', fontsize=12)
    ax_stab.grid(alpha=0.05)

    for ax in [ax_main, ax_phase, ax_energy, ax_stab]:
        ax.set_facecolor('#020202')
        ax.tick_params(colors='#888888', labelsize=8)
        for spine in ax.spines.values(): spine.set_color('#222222')

    plt.tight_layout()
    save_path = "Code/N_Core/QHO_RealData_Impeccable.png"
    plt.savefig(save_path, dpi=250, facecolor='#020202')
    print(f"SUCCESS: Auditoria Impecável salva em: {save_path}")

if __name__ == "__main__":
    run_impeccable_qho_audit()
