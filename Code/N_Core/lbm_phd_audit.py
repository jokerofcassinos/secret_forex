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
    from fluid_dynamics import LBMFluidDynamics
except ImportError as e:
    print(f"FAIL: fluid_dynamics não encontrado. Erro: {e}")
    sys.exit(1)


def run_lbm_audit():
    print("🌊 Iniciando Auditoria Ph.D. LBM (Smagorinsky & Reynolds)...")
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
    
    # Prepara Motor LBM
    p_min = np.min(prices) - 100
    p_max = np.max(prices) + 100
    
    lbm_tracker = LBMFluidDynamics(p_min, p_max, bins=200, smagorinsky_cs=0.15)
    
    if not lbm_tracker.is_active:
        print("Motor C++ lbm_engine inativo.")
        mt5.shutdown()
        return

    print("Processando histórico termodinâmico de fluidos...")
    
    squeeze_hist = []
    pressure_hist = []
    reynolds_hist = []
    
    # Simulação passo a passo
    for i in range(100, len(df)):
        sub_df = df.iloc[:i]
        l_den, l_vel, l_press, l_rey = lbm_tracker.process_tick_stream(sub_df.tail(5), steps=2)
        
        # Pega as métricas locais do instante i
        curr_idx = lbm_tracker.price_to_index(prices[i-1])
        start = max(0, curr_idx - 2)
        end = min(200, curr_idx + 3)
        
        local_p = np.max(l_press[start:end]) if l_press is not None else 0
        local_r = np.max(l_rey[start:end]) if l_rey is not None else 0
        
        pressure_hist.append(local_p)
        reynolds_hist.append(local_r)
        
        # Detecta zona
        sig = lbm_tracker.detect_squeeze_rupture(sub_df.tail(150), l_den, l_vel, l_press, l_rey, 0)
        
        val = 0
        if sig == "BOSONIC_SQUEEZE": val = 3
        elif sig == "FLUID_RUPTURE_BULL": val = 1
        elif sig == "FLUID_RUPTURE_BEAR": val = 2
        
        squeeze_hist.append(val)
        
    # Preenche o início com zeros
    squeeze_hist = [0]*100 + squeeze_hist
    pressure_hist = [0]*100 + pressure_hist
    reynolds_hist = [0]*100 + reynolds_hist

    print("Cálculos físicos concluídos. Gerando espectroscopia gráfica LBM...")

    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    
    time_x = np.arange(len(df))
    
    # [AX 1] Preço e Squeezes
    axs[0].plot(time_x, prices, color='white', linewidth=1.5, label='Price (GER40)', zorder=10)
    axs[0].set_title('LBM ASI-5: Smagorinsky Turbulence & Bosonic Squeezes', fontsize=14, color='deepskyblue')
    
    # Desenha as Caixas LBM
    box_start = -1
    box_val = 0
    for i in range(len(squeeze_hist)):
        if squeeze_hist[i] != box_val:
            if box_val != 0 and box_start != -1:
                # Fim da caixa
                max_h = np.max(prices[box_start:i]) + 20
                min_l = np.min(prices[box_start:i]) - 20
                color = 'deepskyblue' if box_val == 1 else ('darkviolet' if box_val == 2 else 'gold')
                alpha = 0.4 if box_val == 3 else 0.2
                rect = patches.Rectangle((box_start, min_l), i - box_start, max_h - min_l, linewidth=2, edgecolor=color, facecolor=color, alpha=alpha, zorder=1)
                axs[0].add_patch(rect)
                
            box_start = i
            box_val = squeeze_hist[i]

    # [AX 2] Pressão Interna
    axs[1].plot(time_x, pressure_hist, color='magenta', linewidth=1.0, label='Local Pressure Gradient ($P = \\rho c_s^2$)')
    axs[1].set_ylabel('Fluid Pressure')
    axs[1].legend(loc='upper left')
    
    # [AX 3] Reynolds Number
    axs[2].plot(time_x, reynolds_hist, color='gold', linewidth=1.2, label='Dynamic Reynolds Number ($Re$)')
    axs[2].axhline(5.0, color='red', linestyle='--', alpha=0.5, label='Turbulence Threshold (5.0)')
    axs[2].fill_between(time_x, 0, reynolds_hist, color='gold', alpha=0.2)
    axs[2].set_ylabel('Reynolds Number')
    axs[2].legend(loc='upper left')

    plt.tight_layout()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'LBM_Smagorinsky_Audit.png'))
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Artefato visual gerado: {output_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_lbm_audit()