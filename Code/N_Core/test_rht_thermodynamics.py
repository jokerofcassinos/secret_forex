import os
import sys
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
from datetime import datetime

# [BOOTLOADER]
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
        os.add_dll_directory(root_path)
    except: pass

import rht_engine
from Code.N_Core.live_rht import LiveRHTTracker

def run_thermodynamic_visual_audit():
    print("NEXUS RHT :: Iniciando Auditoria Visual Termodinamica...")
    
    if not mt5.initialize():
        print("[ERROR] Erro ao conectar ao MT5")
        return

    symbol = "GER40.cash"
    lookback = 400
    threshold = 0.7
    
    tracker = LiveRHTTracker(symbol=symbol, lookback=lookback)
    
    # 1. Obtenção e Alinhamento de Dados (Mimetizando o loop real)
    dfs = {}
    for name, tf in tracker.timeframes.items():
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, lookback + 100)
        if rates is None: continue
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        dfs[name] = df[['close']].rename(columns={'close': f'{name}_close'})

    # Alinhamento pelo M5
    df_base = dfs['M5']
    for name in ['M15', 'H1', 'D1']:
        df_base = df_base.join(dfs[name], how='left')
        df_base[f'{name}_close'] = df_base[f'{name}_close'].ffill()

    df_h2 = dfs['M5']['M5_close'].resample('2h').last().dropna().to_frame(name='H2_close')
    df_base = df_base.join(df_h2, how='left')
    df_base['H2_close'] = df_base['H2_close'].ffill()
    df_base = df_base.ffill().bfill().tail(lookback)

    # 2. Processamento Tensorial
    tensor_matrix = []
    for tf in ['M5', 'M15', 'H1', 'H2', 'D1']:
        col = f"{tf}_close"
        log_ret = np.log(df_base[col] / df_base[col].shift(1)).fillna(0)
        z = (log_ret - log_ret.rolling(20).mean()) / log_ret.rolling(20).std().replace(0, 1e-9).fillna(1e-9)
        tensor_matrix.append(np.clip(z.values, -4.0, 4.0))
        
    tensor_matrix = np.array(tensor_matrix, dtype=np.float64)
    
    # 3. Execução no Novo Motor C++ v2.0
    engine = rht_engine.RHTEngine(tensor_matrix.shape[0], tensor_matrix.shape[1])
    engine.load_tensor_data(tensor_matrix)
    
    # Histórico de Calor (Inércia Térmica)
    heat_history = engine.compute_resonance_history(gamma=0.15)
    
    # Cálculo de Entropia Instantânea (Desordem)
    # Para o gráfico, vamos simular a entropia ao longo do tempo (chamando o estado repetidamente ou via loop)
    entropy_history = []
    flash_points = [] # Indices onde flash != 0
    
    temp_engine = rht_engine.RHTEngine(tensor_matrix.shape[0], 1)
    for i in range(lookback):
        slice_tensor = tensor_matrix[:, i:i+1]
        temp_engine.load_tensor_data(slice_tensor)
        h, s, d, flash = temp_engine.analyze_current_state(threshold=threshold)
        
        # Simulação do consenso para o gráfico
        directions = slice_tensor[:, 0]
        major_dir = 1.0 if np.sum(directions) > 0 else -1.0
        agree = np.sum((directions > 0) == (major_dir > 0))
        consensus = agree / tensor_matrix.shape[0]
        
        entropy_history.append(s)
        # Ignora sinais que não passam no filtro impecável v2.2
        if flash != 0 and consensus >= 0.8:
            flash_points.append(i)

    # --- PLOTAGEM DE ALTA FIDELIDADE ---
    plt.style.use('dark_background')
    fig, (ax_price, ax_heat, ax_entropy) = plt.subplots(3, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [2, 1.2, 0.8]}, sharex=True)
    
    time_axis = np.arange(lookback)
    prices = df_base['M5_close'].values
    
    # Painel 1: Preço e Ignição
    ax_price.plot(time_axis, prices, color='#FFFFFF', alpha=0.9, linewidth=1.5, label='GER40 (M5)')
    for idx in flash_points:
        color = '#00FFB4' if heat_history[idx] > 0 else '#FF3645'
        ax_price.axvline(idx, color=color, alpha=0.3, linestyle='--', linewidth=1)
        ax_price.scatter(idx, prices[idx], color=color, s=80, edgecolors='white', zorder=5)

    ax_price.set_title(f'RHT THERMODYNAMIC AUDIT :: {symbol}', fontsize=16, fontweight='bold', pad=20)
    ax_price.set_ylabel('Price Axis', fontsize=10, color='#888888')
    ax_price.grid(True, alpha=0.05)
    ax_price.legend(loc='upper left', frameon=False)

    # Painel 2: RHT Heat (Calor Acumulado)
    heat_arr = np.array(heat_history)
    ax_heat.fill_between(time_axis, 0, heat_arr, where=(heat_arr > 0), color='#00FFB4', alpha=0.5, label='Bull Accumulation')
    ax_heat.fill_between(time_axis, 0, heat_arr, where=(heat_arr < 0), color='#FF3645', alpha=0.5, label='Bear Accumulation')
    ax_heat.plot(time_axis, heat_arr, color='white', alpha=0.3, linewidth=0.8)
    ax_heat.axhline(threshold, color='#00FFB4', linestyle=':', alpha=0.6)
    ax_heat.axhline(-threshold, color='#FF3645', linestyle=':', alpha=0.6)
    ax_heat.set_ylabel('Quantum Heat (Inertia)', fontsize=10, color='#888888')
    ax_heat.legend(loc='upper left', frameon=False)

    # Painel 3: Entropia de Shannon (Desordem)
    ax_entropy.plot(time_axis, entropy_history, color='#BC80FF', linewidth=1.5, label='Shannon Entropy (S)')
    ax_entropy.fill_between(time_axis, 0, entropy_history, color='#BC80FF', alpha=0.15)
    ax_entropy.axhline(0.2, color='white', linestyle='--', alpha=0.3, label='Coherence Limit')
    ax_entropy.set_ylabel('Entropy (S)', fontsize=10, color='#888888')
    ax_entropy.set_ylim(0, 1.1)
    ax_entropy.legend(loc='upper left', frameon=False)

    # Estética Final
    plt.xticks(np.linspace(0, lookback-1, 10), df_base.index[np.linspace(0, lookback-1, 10).astype(int)].strftime('%H:%M'), rotation=0)
    plt.xlabel('Market Timeline (M5 Align)', fontsize=10, color='#888888')
    plt.tight_layout()
    
    output_path = os.path.join(root_path, "artifacts", "RHT_Thermodynamic_Audit.png")
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f"[SUCCESS] Auditoria salva em: {output_path}")
    
    mt5.shutdown()
    return output_path

if __name__ == "__main__":
    run_thermodynamic_visual_audit()
