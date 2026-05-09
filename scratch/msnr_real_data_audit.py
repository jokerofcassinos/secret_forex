import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import MetaTrader5 as mt5

# [BOOTLOADER] Integração NEXUS
root = os.getcwd()
sys.path.append(root)
bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
if os.name == 'nt' and os.path.exists(bin_path):
    os.add_dll_directory(bin_path)
    if bin_path not in sys.path: sys.path.insert(0, bin_path)

try:
    from Code.N_Core.msnr_alchemist import MSNRAlchemist
    print("NEXUS ONLINE: Alquimista MSNR conectado ao MT5.")
except ImportError:
    print("ERRO: MSNRAlchemist não encontrado.")
    sys.exit()

def real_data_audit_msnr():
    # 1. Conexão com MT5
    if not mt5.initialize():
        print("FALHA: Não foi possível inicializar o MT5.")
        return

    symbol = "BTCUSD" # Ou US30 conforme o foco do workspace
    print(f"[MSNR-REAL] Capturando 500 candles de {symbol}...")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        print("ERRO: Nenhum dado capturado do MT5.")
        return

    df = pd.DataFrame(rates)
    raw_price = df['close'].values
    
    # 2. Aplicar Alquimia MSNR (C++)
    alchemist = MSNRAlchemist(cut_off=0.08) # Poda calibrada para M5 Real
    crystallized_signal, fidelity = alchemist.apply_spectral_alchemy(raw_price)
    
    print(f">> RESSONÂNCIA REAL: {fidelity*100:.2f}%")
    
    # 3. Renderização Visual Ultra-Premium
    plt.figure(figsize=(16, 9), facecolor='#0B0E11')
    ax = plt.gca()
    ax.set_facecolor('#0B0E11')
    
    # Preço Real (Sombra Cyan)
    plt.plot(raw_price, color='#00FFFF', alpha=0.25, label=f'MERCADO REAL ({symbol})', linewidth=1)
    
    # Sinal Cristalizado (Neon Purple)
    plt.plot(crystallized_signal, color='#BD00FF', label='SINAL CRISTALIZADO (MSNR ASI)', linewidth=3)
    
    # Efeito Glow
    for n in range(1, 6):
        plt.plot(crystallized_signal, color='#BD00FF', alpha=0.08, linewidth=3 + n*3)
        
    plt.title(f'NEXUS MSNR :: REAL-TIME SPECTRAL AUDIT\nSignal Fidelity: {fidelity*100:.2f}% | Symbol: {symbol}', color='white', fontsize=18)
    plt.legend(facecolor='#1E222D', edgecolor='white', labelcolor='white', fontsize=12)
    plt.grid(color='#2D3139', linestyle=':', alpha=0.4)
    
    plt.tick_params(colors='white', labelsize=10)
    plt.xlabel('Ticks (M5 Horizon)', color='gray')
    plt.ylabel('Price (Holographic Projection)', color='gray')

    output_path = os.path.join(root, "msnr_real_data_audit_result.png")
    plt.savefig(output_path, dpi=150)
    print(f">> AUDITORIA REAL CONCLUÍDA: {output_path}")
    plt.show()

if __name__ == "__main__":
    real_data_audit_msnr()
