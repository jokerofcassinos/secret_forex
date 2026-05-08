import numpy as np
import matplotlib.pyplot as plt
import sys
import os

if os.name == 'nt' and os.path.exists(r"D:\msys64\mingw64\bin"):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

sys.path.append(r"d:\AI Brain\US30")

import qrw_engine

def run_visual_audit():
    print("AUDIT: QRW BALISTIC ENGINE v6.7")
    
    POSITIONS = 4001
    DECOHERENCE = 0.9999
    SCALE = 0.04
    
    engine = qrw_engine.QRWEngine(POSITIONS)
    engine.set_decoherence(DECOHERENCE)
    
    bars = 800
    skewness_log = []
    variance_log = []
    
    for i in range(bars):
        d = 10.0
        v = 100.0
        s = engine.update_and_get_skew(np.array([d], dtype=float), np.array([v], dtype=float), SCALE)
        var = engine.get_wave_variance()
        skewness_log.append(s)
        variance_log.append(var)
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    ax1.plot(skewness_log, color='cyan', label='Skewness (sigma)')
    ax1.axhline(y=1.2, color='red', linestyle='--', label='Threshold Exhaustion')
    ax1.axhline(y=0.1, color='yellow', linestyle=':', label='Trigger Sniper v6.7')
    ax1.set_title("Quantum Skewness Propagation (800 Bars Rally)")
    ax1.legend(); ax1.grid(alpha=0.2)
    
    ax2.plot(variance_log, color='magenta', label='Variance')
    ax2.set_title("Wave Variance Growth")
    ax2.legend(); ax2.grid(alpha=0.2)
    
    plt.tight_layout()
    save_path = r"d:\AI Brain\US30\qrw_v67_audit.png"
    plt.savefig(save_path)
    print(f"SUCCESS: {save_path}")
    print(f"FINAL SKEWNESS: {skewness_log[-1]:.4f}")
    print(f"FINAL VARIANCE: {variance_log[-1]:.4f}")

if __name__ == "__main__":
    try:
        run_visual_audit()
    except Exception as e:
        print(f"ERROR: {str(e)}")
