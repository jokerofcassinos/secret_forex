import sys
import os
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from live_rht import LiveRHTTracker

def run_phd_audit():
    print("🌌 Iniciando Auditoria Ph.D. RHT (Cattaneo-Lorentz)...")
    if not mt5.initialize():
        print("Erro: MT5 não inicializou.")
        return

    symbol = "GER40.cash"
    lookback = 1000  # Maior amostra para visualizar o comportamento
    
    tracker = LiveRHTTracker(symbol=symbol, lookback=lookback)
    print(f"Coletando matrizes temporais e executando difusão térmica em {symbol}...")
    
    # Executamos o processamento
    status, cache, flash, hist, heat_flux, entropy_field = tracker.process_live_rht()
    
    if "OFFLINE" in status:
        print("Erro: Dados indisponíveis.")
        mt5.shutdown()
        return

    # Pegamos o lorentz field diretamente do engine agora que está instanciado
    try:
        raw_thermo = tracker.rht_engine_instance.get_thermodynamics()
        lorentz_gamma = raw_thermo.get("lorentz_gamma", [])
        ignition = raw_thermo.get("ignition", [])
    except Exception as e:
        print(f"Erro ao extrair Lorentz: {e}")
        mt5.shutdown()
        return

    # Pegamos os preços para plotar no fundo
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, lookback)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    prices = df['close'].values

    # Plotting
    plt.style.use('dark_background')
    fig, axs = plt.subplots(4, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1, 1]})
    
    # Tratamento de tamanhos para evitar erro de shape (O MT5 às vezes retorna arrays menores do que o lookback devido aos finais de semana)
    min_len = min(len(prices), len(heat_flux), len(entropy_field), len(lorentz_gamma), len(ignition))
    prices = prices[-min_len:]
    heat_flux = heat_flux[-min_len:]
    entropy_field = entropy_field[-min_len:]
    lorentz_gamma = lorentz_gamma[-min_len:]
    ignition = ignition[-min_len:]
    
    time_x = np.arange(min_len)
    
    # [AX 1] Preço e Ignição Termodinâmica
    axs[0].plot(time_x, prices, color='white', linewidth=1.5, label='Price (GER40)')
    axs[0].set_title('RHT ASI-5: Topological Thermodynamics & Market Relativistic Heat', fontsize=14, color='cyan')
    
    # Overlay flashes (Ignições)
    buy_flash_x = [i for i, f in enumerate(ignition) if f == 1.0]
    sell_flash_x = [i for i, f in enumerate(ignition) if f == -1.0]
    
    if buy_flash_x:
        axs[0].scatter(buy_flash_x, prices[buy_flash_x], color='lime', s=100, marker='^', label='Bull Condensate (Heat Flash)', zorder=5)
    if sell_flash_x:
        axs[0].scatter(sell_flash_x, prices[sell_flash_x], color='magenta', s=100, marker='v', label='Bear Condensate (Heat Flash)', zorder=5)
        
    axs[0].legend(loc='upper left')

    # [AX 2] Heat Flux (Cattaneo)
    axs[1].plot(time_x, heat_flux, color='orange', linewidth=1.2, label='Cattaneo Thermal Flux (q)')
    axs[1].axhline(0, color='gray', linestyle='--', alpha=0.5)
    axs[1].set_ylabel('Heat Energy')
    axs[1].legend(loc='upper left')
    
    # [AX 3] Entropy Field (Shannon Adaptive)
    axs[2].plot(time_x, entropy_field, color='cyan', linewidth=1.2, label='Shannon Adaptive Entropy (S)')
    axs[2].axhline(0.5, color='gray', linestyle=':', alpha=0.5)
    axs[2].set_ylabel('Entropy')
    axs[2].legend(loc='upper left')

    # [AX 4] Lorentz Gamma (Time Dilation)
    axs[3].plot(time_x, lorentz_gamma, color='lime', linewidth=1.2, label='Lorentz Factor ($\gamma$)')
    axs[3].axhline(1.0, color='gray', linestyle='-', alpha=0.5)
    axs[3].axhline(1.05, color='red', linestyle='--', alpha=0.5, label='Relativistic threshold (1.05)')
    axs[3].set_ylabel('Time Dilation')
    axs[3].legend(loc='upper left')

    plt.tight_layout()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'RHT_Cattaneo_Lorentz_Audit.png'))
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Artefato visual gerado: {output_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_phd_audit()