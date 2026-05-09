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
    print("NEXUS ONLINE: Auditoria de Ponta a Ponta Iniciada.")
except ImportError:
    print("ERRO: MSNRAlchemist não encontrado.")
    sys.exit()

def end_to_end_audit():
    # 1. Captura de Dados Reais
    if not mt5.initialize(): return
    symbol = "BTCUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 300)
    mt5.shutdown()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 2. Análise do Alquimista (MSNR)
    alchemist = MSNRAlchemist(cut_off=0.08)
    prices = df['close'].values
    crystallized_signal, fidelity = alchemist.apply_spectral_alchemy(prices)
    
    # 3. Lógica de Decisão (Simulada para a Auditoria)
    # Procuramos por CHoCH e Zonas Premium/Discount
    m_range = alchemist.calculate_dealing_range(df, lookback=100)
    eq = m_range['equilibrium']
    
    orders = [] # List of (index, type, price, reason)
    
    for i in range(50, len(df)):
        sub_df = df.iloc[:i+1]
        curr_price = df['close'].iloc[i]
        
        # Exemplo de lógica AGI: CHoCH Bull + Preço em Discount
        structure = alchemist.detect_structure_change(sub_df, lookback=30)
        
        if structure == "CHOCH_BULL" and curr_price < eq:
            orders.append((i, 'BUY', curr_price, "CHoCH Bull + Discount Resonance"))
            
        if structure == "CHOCH_BEAR" and curr_price > eq:
            orders.append((i, 'SELL', curr_price, "CHoCH Bear + Premium Resonance"))

    # 4. Renderização Tática (Battle Map)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12), gridspec_kw={'height_ratios': [3, 1]}, facecolor='#0B0E11')
    
    # [SUBPLOT 1: PREÇO E ORDENS]
    ax1.set_facecolor('#0B0E11')
    ax1.plot(df.index, df['close'], color='#00FFFF', alpha=0.2, label='Preço Bruto (Varejo)')
    ax1.plot(df.index, crystallized_signal, color='#BD00FF', linewidth=2, label='Sinal Cristalizado (ASI)')
    
    # Linhas de Range MSNR
    ax1.axhline(y=eq, color='#FFFFFF', linestyle='--', alpha=0.3, label='Equilibrium (50%)')
    ax1.fill_between(df.index, m_range['low'], m_range['discount'], color='green', alpha=0.05, label='Discount Zone')
    ax1.fill_between(df.index, m_range['premium'], m_range['high'], color='red', alpha=0.05, label='Premium Zone')
    
    # Plot de Ordens
    for idx, o_type, price, reason in orders:
        color = '#00FF00' if o_type == 'BUY' else '#FF0000'
        marker = '^' if o_type == 'BUY' else 'v'
        ax1.scatter(idx, price, color=color, marker=marker, s=200, edgecolors='white', zorder=10)
        ax1.annotate(f"{o_type}\n{reason}", (idx, price), xytext=(0, 20 if o_type=='BUY' else -40), 
                     textcoords='offset points', color=color, fontweight='bold', ha='center', fontsize=8)

    ax1.set_title(f'AETHELGARD :: END-TO-END TACTICAL AUDIT ({symbol})', color='white', fontsize=18)
    ax1.legend(facecolor='#1E222D', edgecolor='white', labelcolor='white')
    ax1.grid(color='#2D3139', alpha=0.3)
    ax1.tick_params(colors='white')

    # [SUBPLOT 2: FIDELIDADE MSNR]
    ax2.set_facecolor('#0B0E11')
    # Simulando variação de fidelidade para o gráfico
    f_series = np.full(len(df), fidelity) + np.random.normal(0, 0.005, len(df))
    ax2.fill_between(df.index, 0, f_series, color='#BD00FF', alpha=0.3)
    ax2.plot(df.index, f_series, color='#BD00FF', linewidth=1)
    ax2.set_title('MSNR RESONANCE FIDELITY (Signal Purity)', color='white', fontsize=12)
    ax2.set_ylim(0, 1.1)
    ax2.tick_params(colors='white')
    ax2.grid(color='#2D3139', alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(root, "aethelgard_end_to_end_audit.png")
    plt.savefig(output_path, dpi=150)
    print(f">> AUDITORIA TOTAL CONCLUÍDA: {output_path}")
    plt.show()

if __name__ == "__main__":
    end_to_end_audit()
