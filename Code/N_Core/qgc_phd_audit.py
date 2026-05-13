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
    import qgc_engine
except ImportError as e:
    print(f"FAIL: qgc_engine não encontrado. Erro: {e}")
    sys.exit(1)


def run_qgc_audit():
    print("🌌 Iniciando Auditoria Ph.D. QGC (Hawking Radiation)...")
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
    
    # Prepara dados para a DLL C++
    vols = df['tick_volume'].values
    prices = df['close'].values
    
    atr_series = (df['high'] - df['low']).rolling(14, min_periods=1).mean().fillna(10.0).values
    v_mean = pd.Series(vols).rolling(20, min_periods=1).mean().values
    v_std = pd.Series(vols).rolling(20, min_periods=1).std().replace(0, 1e-9).fillna(1e-9).values
    z_scores = (vols - v_mean) / v_std
    
    m_thr = np.mean(vols) * 1.5 
    
    # Roda o simulador C++ pesado para o laboratório visual
    engine = qgc_engine.QGCEngine()
    try:
         # Vamos popular manualmente igual o QuantumGlassNode
         active_hist = []
         gravity_pull_hist = []
         
         for i in range(len(df)):
             if z_scores[i] > 2.0:
                 engine.add_zone(prices[i], z_scores[i] * 2.0, float(i))
             
             engine.update_evaporation(float(i), prices[i], atr_series[i])
             
             gravity_pull_hist.append(engine.calculate_gravity_pull(prices[i]))
             # Copia estado atual (snapshot)
             zones_now = engine.get_active_zones()
             snapshot = [{"price": z["price"], "mass": z["mass"], "ratio": z["ratio"], "age": z["age"]} for z in zones_now]
             active_hist.append(snapshot)
             
    except Exception as e:
         print(f"Erro no Motor QGC: {e}")
         mt5.shutdown()
         return

    print("Cálculos físicos concluídos. Gerando espectroscopia gráfica...")

    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    
    time_x = np.arange(len(df))
    
    # [AX 1] Preço e Decaimento de Massa Institucional (As Fitas)
    axs[0].plot(time_x, prices, color='white', linewidth=1.5, label='Price (GER40)', zorder=10)
    axs[0].set_title('QGC ASI-5: Relativistic Hawking Decay & Institutional Mass Splatting', fontsize=14, color='magenta')
    
    # Desenha as fitas QGC baseadas na retenção
    for i in range(0, len(df), 2): # Amostragem a cada 2 barras para clareza
        zones = active_hist[i]
        for z in zones:
            if z["ratio"] < 0.05: continue
            
            p_center = z["price"]
            mass_ratio = z["ratio"] # 1.0 (Full) -> 0.0 (Evaporated)
            
            # Cor: Começa intenso (amarelo/branco) desvanece para Ciano escuro
            alpha = max(0.05, mass_ratio)
            color = (0.0, 1.0, 1.0, alpha) # Ciano com alpha
            
            # Altura (Espessura da fita) baseada na massa original
            thickness = max(0.5, (z["mass"] / 5.0) * mass_ratio)
            
            rect = patches.Rectangle((i, p_center - thickness), 2, thickness*2, linewidth=0, facecolor=color, zorder=1)
            axs[0].add_patch(rect)
            
    axs[0].legend(loc='upper left')

    # [AX 2] Z-Score de Volume Dinâmico (As ignições)
    axs[1].plot(time_x, z_scores, color='lime', linewidth=1.0, label='Dynamic Volume Z-Score')
    axs[1].axhline(2.0, color='red', linestyle='--', alpha=0.5, label='Ignition Threshold (2.0)')
    axs[1].set_ylabel('Sigma ($\sigma$)')
    axs[1].legend(loc='upper left')
    
    # [AX 3] Força Gravitacional Total do Condensado sobre o Preço
    axs[2].plot(time_x, gravity_pull_hist, color='cyan', linewidth=1.2, label='Total Gravitational Pull')
    axs[2].fill_between(time_x, 0, gravity_pull_hist, color='cyan', alpha=0.2)
    axs[2].set_ylabel('Gravity Force')
    axs[2].legend(loc='upper left')

    plt.tight_layout()
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'QGC_Hawking_Lorentz_Audit.png'))
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Artefato visual gerado: {output_path}")
    
    mt5.shutdown()

if __name__ == "__main__":
    run_qgc_audit()