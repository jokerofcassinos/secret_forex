import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
import os
import sys

# Adiciona paths para encontrar o motor C++
sys.path.append(os.getcwd())

if os.name == 'nt':
    mingw_bin = r"D:\msys64\mingw64\bin"
    if os.path.exists(mingw_bin):
        os.add_dll_directory(mingw_bin)

try:
    from Code.N_Core.quantum_walk import QRWTracker
except ImportError as e:
    print(f"ERRO: Motor QRW não encontrado. Detalhes: {e}")
    sys.exit()

def plot_candles(ax, df):
    """Renderiza Candlesticks com estética Stealth."""
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    
    col_up = '#00ff9d'
    col_down = '#ff0055'
    
    # Wicks
    ax.vlines(df.index, df.low, df.high, color='white', linewidth=0.5, alpha=0.3)
    
    # Bodies
    ax.bar(up.index, up.close - up.open, 0.6, bottom=up.open, color=col_up, edgecolor=col_up, linewidth=0.5, alpha=0.9)
    ax.bar(down.index, down.open - down.close, 0.6, bottom=down.close, color=col_down, edgecolor=col_down, linewidth=0.5, alpha=0.9)

def run_impeccable_audit(parquet_path):
    print(f"--- INICIANDO AUDITORIA ZENITH v3.2 :: {os.path.basename(parquet_path)} ---")
    
    # 1. Carregamento de Dados
    df = pd.read_parquet(parquet_path)
    start_idx = max(0, len(df) // 2 - 100)
    df_sample = df.iloc[start_idx : start_idx + 180].copy()
    df_sample.reset_index(drop=True, inplace=True)
    
    # 2. Processamento Quântico
    tracker = QRWTracker(positions=401, decoherence=0.997)
    skew_history = []
    var_history = []
    prob_matrix = [] # Para o Heatmap
    
    print("Simulando evolução da função de onda v7.2...")
    for i in range(len(df_sample)):
        # Processamento incremental para simular LIVE real
        d = df_sample['close'].iloc[i] - df_sample['open'].iloc[i]
        v = df_sample['tick_volume'].iloc[i] if 'tick_volume' in df_sample.columns else 1.0
        
        # Escala dinâmica baseada no ATR local para normalização do bias
        recent_atr = (df_sample['high'] - df_sample['low']).iloc[max(0, i-14):i+1].mean()
        scale = 1.0 / (recent_atr * 0.4 + 1e-9)
        
        skew = tracker.engine.update_and_get_skew(np.array([d], dtype=float), np.array([v], dtype=float), scale)
        variance = tracker.engine.get_wave_variance()
        coherence = tracker.engine.get_coherence()
        
        skew_history.append(skew)
        var_history.append(variance)
        prob_matrix.append(tracker.engine.get_probability_distribution())
        
    prob_matrix = np.array(prob_matrix).T 
    
    # 3. Estética Premium
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 14), facecolor='#050505')
    gs = GridSpec(6, 3, figure=fig, height_ratios=[3, 1, 1, 1, 1.5, 0.5], width_ratios=[1, 1, 0.4])
    
    # --- [AX 0: PRICE ACTION & SINGULARITY DOTS] ---
    ax0 = fig.add_subplot(gs[0, :2])
    ax0.set_facecolor('#050505')
    plot_candles(ax0, df_sample)
    
    bull_signals = []
    bear_signals = []
    singularity_bull = []
    singularity_bear = []
    
    for i in range(2, len(skew_history)):
        curr_s = skew_history[i]
        prev_s = skew_history[i-1]
        curr_v = var_history[i]
        curr_c = np.mean(np.max(prob_matrix[:, max(0, i-5):i+1], axis=0)) # Local Coherence
        curr_h = -np.sum(prob_matrix[:, i] * np.log(prob_matrix[:, i] + 1e-12))
        
        # 1. SINGULARIDADE (Exausto Extrema): Drift Alto + Entropia Alta
        if abs(curr_s) > 0.08 and curr_h > 2.8:
            if curr_s > 0: 
                singularity_bear.append(i)
                print(f"SINGULARITY BEAR detected at bar {i}: skew={curr_s:.4f}, entropy={curr_h:.2f}")
            else: 
                singularity_bull.append(i)
                print(f"SINGULARITY BULL detected at bar {i}: skew={curr_s:.4f}, entropy={curr_h:.2f}")
            
        # 2. FLUXO (Accumulation/Distribution): Drift Persistente
        elif curr_s > 0.02 and prev_s <= 0.02: 
            bull_signals.append(i)
            print(f"FLOW BULL detected at bar {i}: skew={curr_s:.4f}")
        elif curr_s < -0.02 and prev_s >= -0.02: 
            bear_signals.append(i)
            print(f"FLOW BEAR detected at bar {i}: skew={curr_s:.4f}")
    
    ax0.scatter(bull_signals, df_sample['low'].iloc[bull_signals] - 15, marker='^', s=40, color='#00ff9d', alpha=0.6)
    ax0.scatter(bear_signals, df_sample['high'].iloc[bear_signals] + 15, marker='v', s=40, color='#ff0055', alpha=0.6)
    
    # Singularidades com Glow Neon
    ax0.scatter(singularity_bull, df_sample['low'].iloc[singularity_bull] - 25, marker='D', s=120, facecolors='none', edgecolors='#00ffff', linewidth=2, label='Singularity Bottom')
    ax0.scatter(singularity_bear, df_sample['high'].iloc[singularity_bear] + 25, marker='D', s=120, facecolors='none', edgecolors='#ff0055', linewidth=2, label='Singularity Top')
    
    ax0.set_title("NEXUS ZENITH v7.2 :: GER40 QUANTUM SINGULARITY AUDIT", fontsize=16, fontweight='bold', color='#00d4ff', pad=25)
    ax0.grid(color='white', alpha=0.03)
    
    # --- [AX 1: SKEWNESS (DIRECTIONAL BIAS)] ---
    ax1 = fig.add_subplot(gs[1, :2], sharex=ax0)
    ax1.set_facecolor('#050505')
    ax1.plot(skew_history, color='#00d4ff', linewidth=1.5, alpha=0.9)
    ax1.fill_between(range(len(df_sample)), skew_history, 0, where=np.array(skew_history)>0, color='#00ff9d', alpha=0.1)
    ax1.fill_between(range(len(df_sample)), skew_history, 0, where=np.array(skew_history)<0, color='#ff0055', alpha=0.1)
    ax1.set_ylabel("SKEW (σ)", fontsize=10, color='#00d4ff')
    ax1.axhline(0, color='white', alpha=0.2, linewidth=0.5)
    
    # --- [AX 2: WAVE VARIANCE (ENTROPY)] ---
    ax_var = fig.add_subplot(gs[2, :2], sharex=ax0)
    ax_var.set_facecolor('#050505')
    ax_var.plot(var_history, color='#bd00ff', linewidth=1.2)
    ax_var.set_ylabel("VAR (σ²)", fontsize=10, color='#bd00ff')
    ax_var.fill_between(range(len(df_sample)), var_history, min(var_history), color='#bd00ff', alpha=0.05)
    
    # --- [AX 3: QUANTUM COHERENCE (SIGNAL PURITY)] ---
    ax_coh = fig.add_subplot(gs[3, :2], sharex=ax0)
    ax_coh.set_facecolor('#050505')
    coherence_history = [np.max(prob_matrix[:, t]) for t in range(prob_matrix.shape[1])]
    ax_coh.plot(coherence_history, color='#00ffba', linewidth=1.2)
    ax_coh.set_ylabel("COHERENCE", fontsize=10, color='#00ffba')
    ax_coh.fill_between(range(len(df_sample)), coherence_history, 0, color='#00ffba', alpha=0.05)
    ax_coh.axhline(0.1, color='red', alpha=0.3, linestyle='--', linewidth=0.8) # Decoherence threshold
    
    # --- [AX 4: WAVE HEATMAP] ---
    ax2 = fig.add_subplot(gs[4, :2], sharex=ax0)
    center = 200
    grid_slice = prob_matrix[center-70 : center+70, :]
    norm = mcolors.PowerNorm(gamma=0.5, vmin=1e-6, vmax=np.max(grid_slice))
    ax2.imshow(grid_slice, aspect='auto', origin='lower', cmap='magma', norm=norm, alpha=0.95)
    ax2.set_title("QUANTUM PROBABILITY DENSITY (PHASE SPACE)", fontsize=11, color='#bd00ff')
    
    # --- [AX 5: TELEMETRY HUD] ---
    ax_hud = fig.add_subplot(gs[0:5, 2])
    ax_hud.set_facecolor('#0a0a0a')
    ax_hud.set_xticks([]); ax_hud.set_yticks([])
    
    avg_coh = np.mean(coherence_history) * 100
    total_ent = -np.sum(prob_matrix * np.log(prob_matrix + 1e-12)) / len(df_sample)
    
    hud_text = (
        " NEXUS ASI v3.2.1\n"
        " QRW ENGINE: ACTIVE\n"
        " ────────────────────────\n"
        f" AVG COHERENCE: {avg_coh:.2f}%\n"
        f" SYS ENTROPY: {total_ent:.4f} H\n"
        f" PEAK SKEW: {np.max(np.abs(skew_history)):.2f} σ\n"
        " ────────────────────────\n"
        " [DETECTION NODES]\n"
        f" ACCUMULATION: {len(bull_signals)}\n"
        f" DISTRIBUTION: {len(bear_signals)}\n"
        f" SINGULARITY T: {len(singularity_bear)}\n"
        f" SINGULARITY B: {len(singularity_bull)}\n"
        " ────────────────────────\n"
        " STATUS: IMPECCABLE\n"
        " MODE: SINGULARITY SCAN"
    )
    
    ax_hud.text(0.08, 0.95, hud_text, transform=ax_hud.transAxes, 
                family='monospace', fontsize=12, color='#00d4ff', verticalalignment='top')
    
    # Borda decorativa no HUD
    for spine in ax_hud.spines.values():
        spine.set_color('#00d4ff')
        spine.set_alpha(0.3)
    
    plt.tight_layout()
    output_path = "d:/AI Brain/US30/qrw_visual_audit_impeccable.png"
    plt.savefig(output_path, dpi=200, facecolor='#050505')
    print(f"--- AUDITORIA ZENITH CONCLUÍDA :: IMAGEM SALVA EM {output_path} ---")
    return output_path

if __name__ == "__main__":
    parquet = "d:/AI Brain/US30/Data/Historical/GER40.cash_M5.parquet"
    if os.path.exists(parquet):
        run_impeccable_audit(parquet)
    else:
        print("Dados não localizados.")
