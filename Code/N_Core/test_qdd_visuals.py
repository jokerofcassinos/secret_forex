import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Configuração de Caminhos e DLLs
if sys.platform == 'win32':
    os.add_dll_directory(r"D:\msys64\mingw64\bin")
sys.path.append(os.path.join(os.getcwd(), 'Code', 'CPP_Engine'))

import qdd_engine

def generate_qdd_visuals():
    print("🚀 Gerando Visualização Estratégica RG-QDD...")
    
    # 1. Setup do Motor
    # dim=1, hbar=1.0, gamma=0.04 (baixa dissipação para o teste)
    engine = qdd_engine.QDDEngine(1, 1.0, 0.04)
    
    # 2. Geração de Dados Sintéticos Complexos
    n_points = 1000
    t = np.linspace(0, 50, n_points)
    
    # Sinal Base: Uma tendência senoidal lenta
    base_signal = 100 + 10 * np.sin(t * 0.2)
    
    # Adiciona Ruído Térmico (Decoerência)
    noise = np.random.normal(0, 1.5, n_points)
    
    # Injeção de Eventos Quânticos (Institutional Shocks)
    shocks = np.zeros(n_points)
    shocks[300:320] = np.linspace(0, 15, 20) # Shock 1 (Bull)
    shocks[320:450] = 15 # Patamar de energia
    shocks[700:730] = np.linspace(0, -25, 30) # Shock 2 (Bear)
    shocks[730:850] = -25 # Patamar de energia
    
    price_action = base_signal + noise + shocks
    
    # 3. Processamento via Motor C++
    regime_history = []
    energy_history = []
    
    window_size = 64
    for i in range(window_size, n_points):
        slice_data = price_action[i-window_size:i].astype(np.float64)
        # UV_Cutoff=3 (Renormalização), Threshold=0.2
        res = engine.quantize_regime(slice_data, uv_cutoff=3, energy_threshold=0.2)
        regime_history.append(res['regime_state'])
        energy_history.append(res['energy_level'])
    
    # Preenche o início para bater o tamanho do plot
    regime_history = [0]*window_size + regime_history
    energy_history = [0.0]*window_size + energy_history

    # 4. Plotting
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    plt.subplots_adjust(hspace=0.3)

    # Subplot 1: Price Action & Noise
    ax1.plot(price_action, color='#888888', alpha=0.5, label='Raw Price + Noise')
    ax1.plot(base_signal + shocks, color='white', linewidth=1.5, label='True Institutional Flow')
    ax1.set_title("Onda de Preço: Fluxo Bruto vs. Fluxo Institucional Purificado", color='cyan', fontsize=14)
    ax1.legend()
    ax1.grid(alpha=0.1)

    # Subplot 2: Energy Levels (Quantized)
    ax2.fill_between(range(n_points), energy_history, color='magenta', alpha=0.3, label='Quantum Energy Level')
    ax2.axhline(y=0.2, color='yellow', linestyle='--', alpha=0.5, label='E1 Threshold')
    ax2.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='En Threshold')
    ax2.set_title("Níveis de Energia Efetiva (Pós-Lindblad & Renormalização)", color='cyan', fontsize=14)
    ax2.legend()
    ax2.grid(alpha=0.1)

    # Subplot 3: Discrete Regime States
    regime_arr = np.array(regime_history)
    ax3.fill_between(range(n_points), regime_arr, where=(regime_arr==0), color='gray', alpha=0.5, label='E0 (Thermal/Noise)')
    ax3.fill_between(range(n_points), regime_arr, where=(regime_arr==1), color='lime', alpha=0.5, label='E1 (Laminar Regime)')
    ax3.fill_between(range(n_points), regime_arr, where=(regime_arr>=2), color='orange', alpha=0.5, label='En (High Energy Shock)')
    ax3.set_yticks([0, 1, 2])
    ax3.set_yticklabels(['E0', 'E1', 'En'])
    ax3.set_title("Colapso da Função de Onda: Estados de Regime Quantizados", color='cyan', fontsize=14)
    ax3.legend()
    ax3.grid(alpha=0.1)

    # Estética Dark Mode (Aethelgard Style)
    fig.patch.set_facecolor('#0a0a0a')
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#0a0a0a')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#333333')

    plt.suptitle("NEXUS-QUANT :: RG-QDD ENGINE VALIDATION REPORT", color='white', fontsize=20, fontweight='bold')
    
    save_path = "Docs/05_Estrutura_Corporativa/Setores/Q_MATH/RG_QDD_Regime_Quantization.png"
    plt.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
    print(f"✅ Visualização gerada com sucesso: {save_path}")

if __name__ == "__main__":
    generate_qdd_visuals()
