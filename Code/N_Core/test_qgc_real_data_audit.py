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

from Code.N_Core.quantum_glass import QuantumGlassNode

def run_recalibrated_qgc_audit():
    print("[QGC] Gerando Auditoria Recalibrada :: Gravidade Suavizada (Real Data)...")
    
    if not mt5.initialize():
        return
        
    target = "GER40.cash"
    # Pegamos 500 barras para foco total na dinâmica recente
    rates = mt5.copy_rates_from_pos(target, mt5.TIMEFRAME_M1, 0, 500)
    mt5.shutdown()
    
    if rates is None: return

    df = pd.DataFrame(rates)
    node = QuantumGlassNode()
    
    gravity_history = []
    zone_snapshots = []
    
    # Processa o histórico para ver a evolução
    for i in range(50, len(df)):
        window_df = df.iloc[:i+1]
        node.scan_for_condensates(window_df)
        tel = node.get_gravity_telemetry(df['close'].iloc[i])
        gravity_history.append(tel['gravity_pull'])
        zone_snapshots.append(tel['active_zones'])
        
    gravity_history = [0]*50 + gravity_history

    # --- SETUP VISUAL IMPECÁVEL v2 ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 12), facecolor='#010101')
    gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])
    
    ax_main = fig.add_subplot(gs[0])
    ax_grav = fig.add_subplot(gs[1])
    ax_decay = fig.add_subplot(gs[2])
    
    # 1. MAIN CHART: PRICE & EVAPORATING ZONES
    ax_main.plot(df.index, df['close'], color='white', linewidth=1.5, alpha=0.9, zorder=5)
    
    # Renderiza Zonas Ativas Finais
    final_zones = zone_snapshots[-1]
    for zone in final_zones:
        # Cor dinâmica: Ciano para Forte, Magenta para Evaporando
        color = '#00f2ff' if zone['ratio'] > 0.6 else '#ff00ff'
        ax_main.axhline(zone['price'], color=color, alpha=zone['ratio']*0.5, 
                       linewidth=max(1, zone['mass']*1.5), zorder=1)
        ax_main.text(0, zone['price'], f"Mass: {zone['mass']:.2f} (Rel: {zone['ratio']:.1%})", 
                    color=color, alpha=0.6, fontsize=9, fontweight='bold')

    ax_main.set_title("NEXUS QGC RECALIBRATED :: QUANTUM LIQUIDITY GLASS v2", color='cyan', fontsize=18, loc='left', pad=20)
    ax_main.grid(alpha=0.05)

    # 2. SMOOTHED GRAVITY PULL (F)
    ax_grav.plot(df.index, gravity_history, color='#ffaa00', linewidth=2, label='Gravitational Field Intensity')
    ax_grav.fill_between(df.index, gravity_history, 0, color='#ffaa00', alpha=0.15)
    ax_grav.set_title("QUANTUM GRAVITATIONAL FIELD (NO SINGULARITIES)", color='#ffaa00', fontsize=13)
    ax_grav.set_facecolor('#050505')
    ax_grav.grid(alpha=0.05)

    # 3. MASS SPECTROMETRY (Evolution)
    # Mostra a soma das massas ativas ao longo do tempo (Dinamismo da rede)
    total_mass_history = [sum([z['mass'] for z in snap]) for snap in zone_snapshots]
    total_mass_history = [0]*50 + total_mass_history
    ax_decay.plot(df.index, total_mass_history, color='#00ff88', linewidth=2, label='Network Total Mass')
    ax_decay.fill_between(df.index, total_mass_history, 0, color='#00ff88', alpha=0.1)
    
    ax_decay.set_title("SYNAPSE LOAD: TOTAL ACTIVE LIQUIDITY MASS", color='#00ff88', fontsize=13)
    ax_decay.grid(alpha=0.05)

    for ax in [ax_main, ax_grav, ax_decay]:
        ax.set_facecolor('#010101')
        ax.tick_params(colors='#666666', labelsize=9)
        for spine in ax.spines.values(): spine.set_color('#1a1a1a')

    plt.tight_layout()
    save_path = "Code/N_Core/QGC_RealData_Impeccable.png"
    plt.savefig(save_path, dpi=250, facecolor='#010101')
    print(f"SUCCESS: Auditoria Recalibrada QGC salva em: {save_path}")

if __name__ == "__main__":
    run_recalibrated_qgc_audit()
