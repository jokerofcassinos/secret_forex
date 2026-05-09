import pandas as pd
import numpy as np
import os
import sys

# Simular caminhos do Aethelgard
root = os.getcwd()
sys.path.insert(0, root)

from Code.N_Core.msnr_alchemist import MSNRAlchemist

print("Iniciando Teste de Estresse MSNR...")

# 1. Criar dados fake realistas
n_bars = 1000
df = pd.DataFrame({
    'time': range(n_bars),
    'open': np.random.normal(18000, 50, n_bars),
    'high': np.random.normal(18050, 50, n_bars),
    'low': np.random.normal(17950, 50, n_bars),
    'close': np.random.normal(18000, 50, n_bars),
    'tick_volume': np.random.randint(100, 1000, n_bars)
})

try:
    alchemist = MSNRAlchemist()
    print("Alchemist Criado.")
    
    # Simular o loop do Swarm
    for i in range(10):
        print(f"Iteração {i}...")
        msnr_filt, msnr_fid = alchemist.apply_spectral_alchemy(df['close'].values)
        print(f"Fidelity: {msnr_fid:.4f}")
        
        msnr_struct = alchemist.detect_structure_change(df, lookback=20)
        print(f"Structure: {msnr_struct}")
        
        msnr_range = alchemist.calculate_dealing_range(df, lookback=100)
        print(f"Range: {msnr_range['equilibrium']:.2f}")
        
        # Testar formatação f-string (ponto de crash suspeito)
        msnr_sig_val = "0"
        if msnr_struct == "CHOCH_BULL": msnr_sig_val = "1"
        
        msnr_tel = f"{msnr_fid:.4f}|{msnr_sig_val}|{msnr_range['equilibrium']:.2f}|{msnr_range['premium']:.2f}|{msnr_range['discount']:.2f}"
        print(f"Telemetry String OK: {msnr_tel[:30]}...")

    print("\n TESTE MSNR CONCLUÍDO COM SUCESSO.")

except Exception as e:
    print(f" CRASH DETECTADO: {e}")
    import traceback
    traceback.print_exc()
