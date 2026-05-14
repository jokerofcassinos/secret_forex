import sys
import os
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.patches as patches

# Configuração de Caminhos para Import do Engine C++
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
    
    bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")
    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)

if root_path not in sys.path:
    sys.path.insert(0, root_path)
    
bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")
if bin_path not in sys.path:
    sys.path.insert(0, bin_path)

try:
    from yield_governor import YieldGovernor
except ImportError as e:
    print(f"FAIL: yield_governor não encontrado. Erro: {e}")
    sys.exit(1)


def run_cyt_audit():
    print("🌌 Iniciando Auditoria Ph.D. CYT (AdS/CFT - Ricci Tensor)...")
    if not mt5.initialize():
        print("Erro: MT5 não inicializou.")
        return

    symbol = "GER40.cash"
    lookback = 1000  
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, lookback)
    if rates is None or len(rates) == 0:
        print("Erro ao coletar dados do MT5.")
        mt5.shutdown()
        return

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    prices = df['close'].values
    
    cyt_governor = YieldGovernor(danger_window=20)

    print("Processando fluxo topológico e calculando Escalar de Ricci...")
    
    ricci_hist = []
    z_score_hist = []
    danger_hist = []
    
    # Processa barra a barra para simular o tempo real
    for i in range(100, len(df)):
        sub_df = df.iloc[:i]
        
        # Monitora a topologia usando as últimas barras
        metrics = cyt_governor.monitor_topology(sub_df)
        
        ricci = metrics.get('deformation', 0.0)
        z_score = metrics.get('z_score_reverso', 0.0)
        is_danger = 1 if metrics.get('shield_active', False) else 0
        
        ricci_hist.append(ricci)
        z_score_hist.append(z_score)
        danger_hist.append(is_danger)
        
    ricci_hist = [0]*100 + ricci_hist
    z_score_hist = [0]*100 + z_score_hist
    danger_hist = [0]*100 + danger_hist

    print("Cálculos Riemannianos concluídos. Gerando artefato visual CYT...")

    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    
    time_x = np.arange(len(df))
    
    # [AX 1] Preço e Buracos Negros (Danger Zones)
    axs[0].plot(time_x, prices, color='white', linewidth=1.5, label='Price (GER40)', zorder=10)
    axs[0].set_title('CYT ASI-5: AdS/CFT Holographic Principle & Ricci Curvature', fontsize=14, color='tomato')
    
    # Desenha as Caixas de Perigo
    box_start = -1
    for i in range(len(danger_hist)):
        if danger_hist[i] == 1 and box_start == -1:
            box_start = i
        elif danger_hist[i] == 0 and box_start != -1:
            max_h = np.max(prices[box_start:i]) + 20
            min_l = np.min(prices[box_start:i]) - 20
            rect = patches.Rectangle((box_start, min_l), i - box_start, max_h - min_l, linewidth=2, edgecolor='darkred', facecolor='darkred', alpha=0.3, zorder=1)
            axs[0].add_patch(rect)
            box_start = -1

    axs[0].legend(loc='upper left')

    # [AX 2] Ricci Scalar Curvature
    axs[1].plot(time_x, ricci_hist, color='orange', linewidth=1.0, label='Ricci Scalar Curvature ($R$)')
    axs[1].axhline(0, color='gray', linestyle='--', alpha=0.5)
    axs[1].set_ylabel('Curvature')
    axs[1].legend(loc='upper left')
    
    # [AX 3] Absolute Z-Score
    axs[2].plot(time_x, z_score_hist, color='tomato', linewidth=1.2, label='Absolute Z-Score (Gravity Anomaly Depth)')
    axs[2].axhline(2.5, color='red', linestyle='--', alpha=0.5, label='Danger Threshold (2.5)')
    axs[2].fill_between(time_x, 0, z_score_hist, color='tomato', alpha=0.2)
    axs[2].set_ylabel('Absolute Z-Score')
    axs[2].legend(loc='upper left')

    plt.tight_layout()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'CYT_Ricci_Flow_Audit.png'))
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Artefato visual gerado: {output_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_cyt_audit()