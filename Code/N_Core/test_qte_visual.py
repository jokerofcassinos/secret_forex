import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Configuração de Caminhos
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

from Code.N_Core.quantum_tunneling import QuantumTunnelingNode

def run_qte_visual_audit():
    print("[QTE] Iniciando Auditoria de Tunelamento Quântico...")
    node = QuantumTunnelingNode()
    
    # Simulação de uma Barreira de Liquidez (Resistance Wall)
    x = np.linspace(0, 10, 100)
    # Barreira em forma de sino (Liquidez concentrada)
    v_barrier = 2.0 * np.exp(-0.5 * (x - 5)**2 / 0.5**2) 
    
    # Diferentes níveis de energia do preço
    energies = [0.2, 0.8, 1.5, 2.5]
    probabilities = []
    
    for e in energies:
        p = node.engine.calculate_tunneling_probability(100.0, e, v_barrier)
        probabilities.append(p)
    
    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Ax1: A Barreira e as Energias
    ax1.fill_between(x, v_barrier, color='red', alpha=0.3, label='Liquidity Barrier V(x)')
    colors = ['cyan', 'lime', 'yellow', 'white']
    for i, e in enumerate(energies):
        ax1.axhline(y=e, color=colors[i], linestyle='--', label=f'Price Energy E={e} (Prob={probabilities[i]:.2f})')
        
    ax1.set_title("QTE :: Potential Barrier vs Price Energy", color='white', fontsize=14)
    ax1.legend()
    ax1.grid(alpha=0.1)
    
    # Ax2: Probabilidade de Transmissão (Tunelamento)
    ax2.bar([str(e) for e in energies], probabilities, color=colors, alpha=0.7)
    ax2.set_ylim(0, 1.1)
    ax2.set_title("Transmission Coefficient (Tunneling Probability)", color='white', fontsize=14)
    ax2.set_ylabel("Probability T")
    ax2.grid(alpha=0.1)
    
    fig.patch.set_facecolor('#0a0a0a')
    for ax in [ax1, ax2]:
        ax.set_facecolor('#0a0a0a')
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('#333333')

    plt.suptitle("QUANTUM TUNNELING ENGINE (QTE) :: TAKE PROFIT AUDIT", color='white', fontsize=18)
    
    save_path = "Code/N_Core/QTE_Tunneling_Audit.png"
    plt.savefig(save_path, dpi=150)
    print(f"SUCCESS: Auditoria QTE salva em: {save_path}")

if __name__ == "__main__":
    run_qte_visual_audit()
