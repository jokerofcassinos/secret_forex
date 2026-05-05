import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Adiciona o path para importar o módulo quântico anterior e o engine C++
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CPP_Engine')))

if hasattr(os, 'add_dll_directory'):
    try:
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    except FileNotFoundError:
        pass

import rht_engine
from quantum_hologram import QuantumHologramNezus

def run_visual_test():
    print("[N-Core Visuals] Iniciando mapeamento visual da Ressonância Holográfica...")
    
    # Inicializar e processar dados
    hologram = QuantumHologramNezus()
    lookback = 500  # Vamos focar nos últimos 500 ticks para melhor visualização
    hologram.load_and_align_fractals(lookback_steps=lookback)
    hologram.compute_tensors()
    
    num_tf, t_steps = hologram.tensor_matrix.shape
    
    # Injetar no C++
    print(f"[Q-Math Bridge] Calculando linha do tempo de ressonância no C++ ({num_tf}x{t_steps})...")
    rht = rht_engine.RHTEngine(num_tf, t_steps)
    rht.load_tensor_data(hologram.tensor_matrix)
    
    # Extrair histórico completo em vez de apenas o último instante
    resonance_history = rht.compute_resonance()
    
    # --- PLOTAGEM MATPLOTLIB ---
    print("[N-Core Visuals] Gerando gráfico...")
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]}, sharex=True)
    
    # Usar índices sequenciais para evitar gaps de fim de semana na plotagem
    time_axis = np.arange(len(hologram.merged_df))
    time_labels = hologram.merged_df.index.strftime('%m-%d %H:%M')
    
    # 1. Eixo Superior: Ondas de Momentum Individuais (M5 a D1)
    colors = ['#00FFFF', '#FF00FF', '#FFFF00', '#00FF00', '#FF4500']
    for i, tf in enumerate(hologram.timeframes):
        ax1.plot(time_axis, hologram.tensor_matrix[i, :], label=f'{tf} Wave', color=colors[i], alpha=0.7, linewidth=1.2)
        
    ax1.set_title(f'RHT (Ressonância Holográfica de Tensores) - {hologram.symbol}', fontsize=16, fontweight='bold', color='white')
    ax1.set_ylabel('Entropia Normalizada (Z-Score)', color='white')
    ax1.axhline(0, color='white', alpha=0.2, linestyle='--')
    ax1.legend(loc='upper left', frameon=False)
    ax1.grid(True, alpha=0.1)

    # 2. Eixo Inferior: Pulso de Ressonância (O Colapso)
    resonance_arr = np.array(resonance_history)
    
    # Colorir os pulsos (Verde para Bull, Vermelho para Bear)
    bull_mask = resonance_arr > 0
    bear_mask = resonance_arr <= 0
    
    ax2.fill_between(time_axis, 0, resonance_arr, where=bull_mask, color='#00FF00', alpha=0.6, label='Bull Resonance')
    ax2.fill_between(time_axis, 0, resonance_arr, where=bear_mask, color='#FF0000', alpha=0.6, label='Bear Resonance')
    ax2.plot(time_axis, resonance_arr, color='white', alpha=0.5, linewidth=1)
    
    # Linhas de Threshold (Onde o colapso é válido. Ex: 0.6 e -0.6)
    threshold = 0.6
    ax2.axhline(threshold, color='#00FF00', linestyle=':', alpha=0.8, label=f'Threshold (+{threshold})')
    ax2.axhline(-threshold, color='#FF0000', linestyle=':', alpha=0.8, label=f'Threshold (-{threshold})')
    
    ax2.set_ylabel('Energia Quântica (Colapso)', color='white')
    ax2.set_xlabel('Tempo Relativo (Ticks Contínuos - FDS Suprimido)', color='white')
    
    # Formatação do eixo X com os labels de tempo real
    step = max(1, len(time_axis) // 10)
    ax2.set_xticks(time_axis[::step])
    ax2.set_xticklabels(time_labels[::step], rotation=45, ha='right', color='white')
    
    ax2.legend(loc='upper left', frameon=False)
    ax2.grid(True, alpha=0.1)
    
    plt.tight_layout()
    
    # Salvar o gráfico na pasta de visual analytics
    output_dir = r"D:\AI Brain\US30\Docs\03_Ambiente_Executivo"
    output_path = os.path.join(output_dir, "RHT_Visual_Test.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[N-Core Visuals] Mapeamento visual salvo em: {output_path}")
    
    # Tenta abrir automaticamente (Windows)
    try:
        os.startfile(output_path)
    except Exception:
        pass

if __name__ == "__main__":
    run_visual_test()
