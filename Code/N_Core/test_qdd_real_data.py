import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
from datetime import datetime

# Configuração de Caminhos
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

from Code.N_Core.tensor_network import TensorNetworkNode

def get_real_data(symbol="GER40", lookback=1000):
    print(f"[MT5] Conectando para extração de {symbol}...")
    if not mt5.initialize():
        print("FAIL: Falha ao inicializar MT5")
        return None

    # Tenta encontrar o símbolo correto (GER40 ou GER40.cash)
    symbols = mt5.symbols_get()
    found_symbol = None
    for s in symbols:
        if symbol in s.name:
            found_symbol = s.name
            break
    
    if not found_symbol:
        print(f"FAIL: Símbolo {symbol} não encontrado.")
        mt5.shutdown()
        return None
    
    print(f"DEBUG: Usando símbolo real: {found_symbol}")

    # Timeframes para auditoria
    tfs = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15
    }
    
    data_dict = {}
    for name, tf in tfs.items():
        rates = mt5.copy_rates_from_pos(found_symbol, tf, 0, lookback)
        if rates is None or len(rates) == 0:
            print(f"WARN: Falha ao obter dados para {name}")
            continue
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        data_dict[name] = df[['close']]

    mt5.shutdown()
    return data_dict

def run_real_data_audit():
    print("[NEXUS] Iniciando Auditoria Real-Data QDD...")
    symbol = "GER40" 
    raw_data = get_real_data(symbol)
    
    if not raw_data or len(raw_data) < 3:
        print("FAIL: Dados insuficientes para auditoria.")
        return

    node = TensorNetworkNode()
    lookback = node.lookback
    
    # Usaremos o M1 como base de tempo
    base_df = raw_data['M1']
    fidelity_history = []
    
    print(f"[QDD] Processando {len(base_df)} pontos de dados reais...")
    
    for i in range(lookback, len(base_df)):
        window_data = {}
        current_time = base_df.index[i]
        
        for name, df in raw_data.items():
            subset = df[df.index <= current_time].tail(lookback)
            window_data[name] = subset
            
        f = node.calculate_global_alignment(window_data)
        fidelity_history.append(f)
        
    fidelity_history = [0] * (len(base_df) - len(fidelity_history)) + fidelity_history

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    ax1.plot(raw_data['M1'].index, raw_data['M1']['close'], color='cyan', label='M1 (Real Price)', linewidth=1)
    ax1.set_title(f"NEXUS-QUANT :: {symbol} Real-Time Manifold", color='white', fontsize=14)
    ax1.legend()
    ax1.grid(alpha=0.1)
    
    ax2.plot(base_df.index, fidelity_history, color='lime', linewidth=2, label='Real Fidelity (QDD)')
    ax2.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Entanglement Threshold')
    ax2.fill_between(base_df.index, fidelity_history, 0.8, where=(np.array(fidelity_history) >= 0.8), color='lime', alpha=0.3)
    ax2.set_title("Real-Data Coherence Score (Fidelidade Institucional)", color='white', fontsize=14)
    ax2.legend()
    ax2.grid(alpha=0.1)
    
    fig.patch.set_facecolor('#0a0a0a')
    for ax in [ax1, ax2]:
        ax.set_facecolor('#0a0a0a')
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('#333333')

    plt.suptitle(f"QDD TENSOR NETWORK :: REAL DATA AUDIT ({symbol})", color='white', fontsize=20)
    
    save_path = "Code/N_Core/QDD_RealData_Audit.png"
    plt.savefig(save_path, dpi=150)
    print(f"SUCCESS: Auditoria Real-Data salva em: {save_path}")

if __name__ == "__main__":
    run_real_data_audit()
