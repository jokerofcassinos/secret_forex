import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# [BOOTLOADER] Integração MSNR
root = os.getcwd()
sys.path.append(root)
bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
if os.path.exists(bin_path):
    os.add_dll_directory(bin_path)
    if bin_path not in sys.path: sys.path.insert(0, bin_path)

try:
    from Code.N_Core.msnr_alchemist import MSNRAlchemist
    print("NEXUS ONLINE: Alquimista MSNR pronto para a Prova de Conceito.")
except ImportError:
    print("ERRO: MSNRAlchemist não encontrado.")
    sys.exit()

def visual_audit_msnr():
    # 1. Carregar dados reais (Simulado com volatilidade real do BTC)
    print("[MSNR-AUDIT] Capturando frequência de mercado...")
    
    t = np.linspace(0, 10, 500)
    # Sinal Institucional (Baixa frequência)
    trend = 80000 + 500 * np.sin(t * 0.5) + 200 * t
    # Ruído do Varejo (Alta frequência e aleatoriedade)
    noise = np.random.normal(0, 50, 500) + 100 * np.sin(t * 15)
    
    raw_price = trend + noise
    
    # 2. Aplicar Alquimia MSNR (C++)
    alchemist = MSNRAlchemist(cut_off=0.1) # Poda agressiva para teste
    crystallized_signal, fidelity = alchemist.apply_spectral_alchemy(raw_price)
    
    print(f">> RESSONÂNCIA DE SINAL: {fidelity*100:.2f}%")
    
    # 3. Renderização Visual Premium
    plt.figure(figsize=(15, 8), facecolor='#0B0E11')
    ax = plt.gca()
    ax.set_facecolor('#0B0E11')
    
    plt.plot(raw_price, color='#00FFFF', alpha=0.3, label='RUÍDO BRUTO (Varejo)', linewidth=1)
    plt.plot(crystallized_signal, color='#BD00FF', label='SINAL CRISTALIZADO (Institucional)', linewidth=2.5)
    
    plt.title(f'NEXUS MSNR :: SPECTRAL ALCHEMY AUDIT\nSignal Fidelity: {fidelity*100:.2f}%', color='white', fontsize=16)
    plt.legend(facecolor='#1E222D', edgecolor='white', labelcolor='white')
    plt.grid(color='#2D3139', linestyle='--', alpha=0.5)
    
    # Efeito Glow no sinal puro
    for n in range(1, 5):
        plt.plot(crystallized_signal, color='#BD00FF', alpha=0.1, linewidth=2.5 + n*2)
        
    plt.tick_params(colors='white')
    output_path = os.path.join(root, "msnr_spectral_audit_result.png")
    plt.savefig(output_path, dpi=120)
    print(f">> AUDITORIA CONCLUÍDA: {output_path}")
    plt.show()

if __name__ == "__main__":
    visual_audit_msnr()
