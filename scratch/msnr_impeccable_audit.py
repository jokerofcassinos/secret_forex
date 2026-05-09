import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
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
    print("NEXUS ONLINE: Gerando Auditoria Impecável...")
except ImportError:
    print("ERRO: MSNRAlchemist não encontrado.")
    sys.exit()

def draw_candlestick(ax, i, row):
    color = '#26A69A' if row['close'] >= row['open'] else '#EF5350'
    # Wick
    ax.vlines(i, row['low'], row['high'], color=color, linewidth=1)
    # Body
    width = 0.6
    rect = patches.Rectangle((i - width/2, min(row['open'], row['close'])), width, abs(row['close'] - row['open']),
                             facecolor=color, edgecolor=color, zorder=3)
    ax.add_patch(rect)

def impeccable_audit_msnr():
    # 1. Dados Reais MT5
    if not mt5.initialize(): return
    symbol = "BTCUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 70) # Zoom Tático para clareza absoluta
    mt5.shutdown()
    
    df = pd.DataFrame(rates)
    
    # 2. Alquimia MSNR
    alchemist = MSNRAlchemist(cut_off=0.1)
    prices = df['close'].values
    crystallized_signal, fidelity = alchemist.apply_spectral_alchemy(prices)
    m_range = alchemist.calculate_dealing_range(df, lookback=100)
    
    # 3. Simulação de Ordens
    orders = []
    for i in range(50, len(df)):
        sub_df = df.iloc[:i+1]
        structure = alchemist.detect_structure_change(sub_df, lookback=20)
        curr_price = df['close'].iloc[i]
        
        if structure == "CHOCH_BULL" and curr_price < m_range['equilibrium']:
            orders.append((i, 'BUY', curr_price))
        if structure == "CHOCH_BEAR" and curr_price > m_range['equilibrium']:
            orders.append((i, 'SELL', curr_price))

    # 4. Plotagem Ultra-Premium
    fig, ax = plt.subplots(figsize=(18, 10), facecolor='#0B0E11')
    ax.set_facecolor('#0B0E11')
    
    # Zonas de Alquimia (Background)
    ax.axhline(y=m_range['equilibrium'], color='#FFFFFF', linestyle='--', alpha=0.2, label='Equilibrium')
    ax.fill_between([0, len(df)], m_range['low'], m_range['discount'], color='#00FF00', alpha=0.07, label='Discount Zone')
    ax.fill_between([0, len(df)], m_range['premium'], m_range['high'], color='#FF0000', alpha=0.07, label='Premium Zone')
    
    # Desenhar Candlesticks
    for i in range(len(df)):
        draw_candlestick(ax, i, df.iloc[i])
    
    # Sinal MSNR (Overlay Suave)
    ax.plot(crystallized_signal, color='#BD00FF', linewidth=1.5, alpha=0.6, label='MSNR Signal Line', zorder=4)
    
    # Plot de Ordens (Estética TradingView)
    for idx, o_type, price in orders:
        color = '#00FF00' if o_type == 'BUY' else '#FF0000'
        ax.annotate('', xy=(idx, price), xytext=(idx, price - 50 if o_type=='BUY' else price + 50),
                    arrowprops=dict(facecolor=color, edgecolor='white', shrink=0.05, width=4, headwidth=12),
                    zorder=10)
        ax.text(idx, price - 80 if o_type=='BUY' else price + 80, f"MSNR {o_type}", 
                color='white', fontweight='bold', ha='center', fontsize=9, 
                bbox=dict(facecolor=color, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'), zorder=11)

    # Configurações de Estilo
    ax.set_title(f'NEXUS :: MSNR ALCHEMIST IMPECCABLE AUDIT ({symbol})', color='white', fontsize=20, pad=20)
    ax.legend(facecolor='#1E222D', edgecolor='white', labelcolor='white', loc='upper left')
    ax.grid(color='#2D3139', alpha=0.2)
    ax.tick_params(colors='white', labelsize=10)
    ax.set_xlim(-5, len(df)+5)
    
    # Remover bordas
    for spine in ax.spines.values(): spine.set_visible(False)

    output_path = os.path.join(root, "msnr_impeccable_audit.png")
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    print(f">> AUDITORIA IMPECÁVEL CONCLUÍDA: {output_path}")
    plt.show()

if __name__ == "__main__":
    impeccable_audit_msnr()
