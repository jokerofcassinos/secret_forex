import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Configuração de Caminhos e DLLs
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

from Code.N_Core.tensor_network import TensorNetworkNode

def run_tensor_audit():
    print("[QDD] Iniciando Auditoria de Alinhamento Dimensional...")
    node = TensorNetworkNode()
    
    n_points = 500
    t = np.linspace(0, 50, n_points)
    
    # Simulação de 4 Dimensões (Timeframes)
    # M15 (Lento/Macro)
    macro = 100 + 20 * np.sin(t * 0.1)
    # M5 (Médio)
    mid = 100 + 15 * np.sin(t * 0.3)
    # M1 (Rápido)
    fast = 100 + 10 * np.sin(t * 0.6)
    # Scalp (Ruído)
    noise = np.random.normal(0, 2, n_points)
    
    # FASE 1: Caos (Desalinhados)
    # FASE 2: Alinhamento Total (Institutional Pulse)
    alignment_start = 300
    for i in range(alignment_start, n_points):
        # Força todos a seguirem a mesma frequência macro + drift
        mid[i] = macro[i] + np.sin(i*0.1)*2
        fast[i] = macro[i] + np.cos(i*0.1)*1
        
    fidelity_history = []
    
    for i in range(128, n_points):
        data = {
            'Macro': pd.DataFrame({'close': macro[i-128:i]}),
            'Mid': pd.DataFrame({'close': mid[i-128:i]}),
            'Fast': pd.DataFrame({'close': fast[i-128:i]})
        }
        f = node.calculate_global_fidelity(data) if hasattr(node, 'calculate_global_fidelity') else node.calculate_global_alignment(data)
        fidelity_history.append(f)
        
    fidelity_history = [0]*128 + fidelity_history
    
    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    ax1.plot(macro, color='cyan', label='H1 (Macro Wave)', linewidth=2)
    ax1.plot(mid, color='magenta', label='M15 (Mid Wave)', alpha=0.6)
    ax1.plot(fast, color='yellow', label='M5 (Fast Wave)', alpha=0.4)
    ax1.axvline(x=alignment_start, color='white', linestyle='--', label='Dimensional Convergence')
    ax1.set_title("Multi-Timeframe Manifold (Simulado)", color='white', fontsize=14)
    ax1.legend()
    ax1.grid(alpha=0.1)
    
    ax2.plot(fidelity_history, color='lime', linewidth=2, label='Global Fidelity (QDD)')
    ax2.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Entanglement Threshold')
    ax2.fill_between(range(n_points), fidelity_history, 0.8, where=(np.array(fidelity_history) >= 0.8), color='lime', alpha=0.3)
    ax2.set_title("Tensor Coherence Score (Fidelidade do Emaranhamento)", color='white', fontsize=14)
    ax2.legend()
    ax2.grid(alpha=0.1)
    
    fig.patch.set_facecolor('#0a0a0a')
    for ax in [ax1, ax2]:
        ax.set_facecolor('#0a0a0a')
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('#333333')

    plt.suptitle("NEXUS-QUANT :: QDD TENSOR NETWORK AUDIT", color='white', fontsize=20)
    
    save_path = "Code/N_Core/QDD_Tensor_Alignment_Audit.png"
    plt.savefig(save_path, dpi=150)
    print(f"SUCCESS: Auditoria salva em: {save_path}")

import pandas as pd
if __name__ == "__main__":
    run_tensor_audit()
