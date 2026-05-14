import sys
import os
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
    from random_matrix import RandomMatrixTracker
except ImportError as e:
    print(f"FAIL: random_matrix não encontrado. Erro: {e}")
    sys.exit(1)


def run_rmt_audit():
    print("🔮 Iniciando Auditoria Ph.D. RMT (Spectral Alchemist - Marchenko-Pastur)...")
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
    
    rmt_tracker = RandomMatrixTracker(time_steps=100)
    
    if not rmt_tracker.is_active:
        print("Motor C++ rmt_engine inativo.")
        mt5.shutdown()
        return

    print("Processando histórico espectral e limpando ruído browniano...")
    
    signal_hist = []
    power_hist = []
    snr_hist = []
    
    for i in range(100, len(df)):
        sub_df = df.iloc[:i]
        
        # Simula a extração (lbm_velocity = zero array para teste puro de RMT sem peso LBM)
        sig = rmt_tracker.process_spectral_filter(sub_df, lbm_velocity=np.zeros(100))
        
        if rmt_tracker.engine is not None:
            results = rmt_tracker.engine.perform_spectral_cleaning()
            snr = results.get("signal_to_noise", 0.0)
            power = results.get("signal_power", 0.0)
        else:
            snr, power = 0.0, 0.0
            
        power_hist.append(power)
        snr_hist.append(snr)
        
        val = 1 if sig == "SIGNAL_ISOLATED" else 0
        signal_hist.append(val)
        
    signal_hist = [0]*100 + signal_hist
    power_hist = [0]*100 + power_hist
    snr_hist = [0]*100 + snr_hist

    print("Cálculos espectrais concluídos. Gerando artefato visual RMT...")

    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    
    time_x = np.arange(len(df))
    
    # [AX 1] Preço e Isolamento de Sinal
    axs[0].plot(time_x, prices, color='white', linewidth=1.5, label='Price (GER40)')
    axs[0].set_title('RMT ASI-5: Spectral Alchemist (Marchenko-Pastur Noise Clipping)', fontsize=14, color='lime')
    
    # Shade das zonas "Limpas" (Signal Isolated)
    axs[0].fill_between(time_x, np.min(prices), np.max(prices), where=np.array(signal_hist) == 1, color='lime', alpha=0.15, label='Signal Isolated (Noise Cleared)')
    axs[0].legend(loc='upper left')

    # [AX 2] Signal Power
    axs[1].plot(time_x, power_hist, color='cyan', linewidth=1.0, label='Signal Power vs MP Limit')
    axs[1].axhline(1.5, color='red', linestyle='--', alpha=0.5, label='Isolation Threshold (1.5)')
    axs[1].set_ylabel('Power Ratio')
    axs[1].legend(loc='upper left')
    
    # [AX 3] SNR
    axs[2].plot(time_x, snr_hist, color='gold', linewidth=1.2, label='Signal-to-Noise Ratio (Post-Clipping)')
    axs[2].axhline(1.2, color='red', linestyle='--', alpha=0.5, label='SNR Threshold (1.2)')
    axs[2].fill_between(time_x, 0, snr_hist, color='gold', alpha=0.2)
    axs[2].set_ylabel('SNR')
    axs[2].legend(loc='upper left')

    plt.tight_layout()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'RMT_Spectral_Audit.png'))
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Artefato visual gerado: {output_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_rmt_audit()