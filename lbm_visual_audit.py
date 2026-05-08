import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++
if os.name == 'nt' and os.path.exists(r"D:\msys64\mingw64\bin"):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

sys.path.append(os.getcwd())
from Code.N_Core.fluid_dynamics import LBMFluidDynamics

def run_visual_audit(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_H1, count=300):
    print(f"LBM AUDIT :: Conectando ao MT5 para extrair DNA de {symbol}...")
    
    if not mt5.initialize():
        print("[-] Falha ao inicializar MT5")
        return

    # 1. Extração de Dados Reais
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        print(f"[-] Nenhum dado encontrado para {symbol}")
        return

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 2. Inicialização do Motor LBM
    p_min, p_max = df['low'].min() * 0.999, df['high'].max() * 1.001
    lbm = LBMFluidDynamics(p_min, p_max, bins=150)
    
    print(f"LBM AUDIT :: Processando {len(df)} candles no motor de fluidos...")
    
    # Cache para visualização
    densities = []
    signals = []
    
    # Simulação passo a passo
    for i in range(50, len(df)):
        slice_df = df.iloc[:i+1]
        
        # Processa o fluxo (simulando 5 steps por candle para auditoria)
        density, velocity = lbm.process_tick_stream(slice_df.tail(1), steps=5)
        
        if density is not None:
            densities.append(density)
            # Detecta sinais com a nova lógica Sniper
            sig = lbm.detect_squeeze_rupture(slice_df, density, velocity, current_regime=1) # Simula Bull Tsunami
            signals.append((i, df.iloc[i]['close'], sig))
            
    print("LBM AUDIT :: Gerando representação visual da Matrix...")

    
    # 3. Plotagem de Alta Fidelidade
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]}, facecolor='#0f1219')
    
    # Preço e Sinais
    ax1.set_facecolor('#0f1219')
    ax1.plot(df['time'], df['close'], color='#454d5f', alpha=0.5, label='Preço (DNA)')
    
    for idx, price, sig in signals:
        t = df['time'].iloc[idx]
        if sig == "FLUID_RUPTURE_BULL":
            ax1.scatter(t, price, color='#00e5ff', marker='^', s=100, edgecolors='white', label='Rupture Bull' if 'Rupture Bull' not in [l.get_label() for l in ax1.get_lines()] else "")
            ax1.axvspan(df['time'].iloc[idx-1], df['time'].iloc[idx], color='#00e5ff', alpha=0.2)
        elif sig == "FLUID_RUPTURE_BEAR":
            ax1.scatter(t, price, color='#d500f9', marker='v', s=100, edgecolors='white')
            ax1.axvspan(df['time'].iloc[idx-1], df['time'].iloc[idx], color='#d500f9', alpha=0.2)
        elif sig == "BOSONIC_SQUEEZE":
            ax1.scatter(t, price, color='#ffea00', marker='o', s=120, edgecolors='black')
            ax1.axvspan(df['time'].iloc[idx-1], df['time'].iloc[idx], color='#ffea00', alpha=0.3)

    ax1.set_title(f"AETHELGARD LBM AUDIT :: {symbol}", color='white', fontsize=14)
    ax1.tick_params(colors='white')
    ax1.grid(alpha=0.1)

    # Calor de Densidade (O que a máquina vê)
    if densities:
        density_matrix = np.array(densities).T
        im = ax2.imshow(density_matrix, aspect='auto', cmap='magma', extent=[0, len(densities), p_min, p_max], origin='lower')
        plt.colorbar(im, ax=ax2, label='Massa Volumétrica')
    
    ax2.set_title("LBM DENSITY MATRIX (Institutional Liquidity Accumulation)", color='white', fontsize=12)
    ax2.set_facecolor('#0f1219')
    ax2.tick_params(colors='white')
    
    plt.tight_layout()
    output_path = "lbm_audit_result.png"
    plt.savefig(output_path, dpi=200)
    print(f"AUDITORIA CONCLUIDA! Imagem salva em: {os.path.abspath(output_path)}")
    plt.show()


if __name__ == "__main__":
    # Tenta BTCUSD por padrão, mas aceita argumentos
    asset = sys.argv[1] if len(sys.argv) > 1 else "BTCUSD"
    run_visual_audit(symbol=asset)
