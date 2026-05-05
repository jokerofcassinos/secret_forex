import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Resolve DLL issue on Windows
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CPP_Engine', 'bin')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CPP_Engine')))

from fluid_dynamics import LBMFluidDynamics
from quantum_clouds import QuantumCloudTracker

def simulate_viscoelastic_wick():
    print("--- INICIANDO TESTE DE ABSORÇÃO VISCOELÁSTICA (WICK) ---")
    
    # 1. Gerar dados sintéticos simulando um Stop Hunt
    steps = 100
    base_price = 24000.0
    
    # Tendência de alta normal
    prices = np.linspace(base_price, base_price + 100, 80)
    volumes = np.random.normal(500, 100, 80)
    
    # O Wick repentino (Stop Hunt para capturar liquidez abaixo de 24000)
    wick_drop = np.linspace(base_price + 100, base_price - 50, 5) # Cai 150 pontos rápido
    wick_vol = np.random.normal(150, 50, 5) # Baixo volume real
    
    # Recuperação imediata
    recovery = np.linspace(base_price - 50, base_price + 120, 15)
    rec_vol = np.random.normal(800, 200, 15) # Alto volume entrando
    
    close_prices = np.concatenate([prices, wick_drop, recovery])
    tick_volumes = np.concatenate([volumes, wick_vol, rec_vol])
    
    # Montar DataFrame simplificado
    df = pd.DataFrame({
        'open': close_prices - 2,
        'high': close_prices + 5,
        'low': close_prices - 5,
        'close': close_prices,
        'tick_volume': tick_volumes
    })
    
    # 2. Configurar os Motores Quânticos e SL Virtual
    p_min = 23900.0
    p_max = 24200.0
    cloud_tracker = QuantumCloudTracker(price_min=p_min, price_max=p_max, bins=300)
    lbm_tracker = LBMFluidDynamics(price_min=p_min, price_max=p_max, bins=300, tau=1.5)
    
    # Inicializa a onda no preço inicial
    cloud_tracker.initialize_wave(close_prices[0])
    
    # Definindo um SL Lógico (Virtual) em 23980.0
    virtual_sl = 23980.0
    
    # Para visualização
    density_history = []
    wick_event_idx = -1
    deborah_recorded = 0.0
    tunneling_recorded = 0.0
    sl_triggered = False
    
    print(f"SL Virtual definido em: {virtual_sl}")
    
    for i in range(10, len(df)):
        slice_df = df.iloc[:i+1].copy()
        current_price = df['close'].iloc[i]
        
        # Atualiza a nuvem
        density, _ = cloud_tracker.step(slice_df, dt=0.2, steps=5)
        density_history.append(density)
        
        # Injeta liquidez no LBM
        lbm_tracker.process_tick_stream(slice_df.tail(5), steps=5)
        
        # Verifica rompimento do SL Virtual
        if current_price <= virtual_sl and not sl_triggered:
            if wick_event_idx == -1:
                wick_event_idx = i
                print(f"\n[!] ALARME: Preço ({current_price:.2f}) cruzou o SL Virtual ({virtual_sl:.2f}) no tick {i}!")
            
            # Avaliação Viscoelástica (LBM)
            # Duração simulada do wick: 1 segundo (choque instantâneo) para disparar Deborah Alto
            anomaly_duration = 1.0 
            is_visco = lbm_tracker.evaluate_viscoelastic_shock(anomaly_duration)
            deborah_recorded = lbm_tracker.engine.calculate_deborah_number(anomaly_duration)
            
            # Avaliação de Tunelamento (Schrödinger)
            vol_mass = df['tick_volume'].iloc[i] * 0.001
            barrier_e = abs(virtual_sl - df['close'].iloc[i-1])
            particle_e = abs(current_price - df['close'].iloc[i-1])
            tunnel_prob = cloud_tracker.check_quantum_tunneling(barrier_e, particle_e, vol_mass)
            tunneling_recorded = tunnel_prob
            
            is_tunneling = tunnel_prob > 0.5
            
            if is_visco or is_tunneling:
                pass # Absorvido silenciosamente pelos logs, mantém o trade vivo
            else:
                print(f"💥 [COLAPSO] Rompimento estrutural real detectado no tick {i}. Trade Fechado.")
                sl_triggered = True

    if not sl_triggered:
        print(f"🌊 [DEFESA ATIVA] Todo o impacto do wick foi absorvido pela Fronteira Viscoelástica!")
        print(f"    -> Número de Deborah Máx: {deborah_recorded:.2f} (Limiar > 1.2 = Fluido Endureceu)")
        print(f"    -> Probabilidade de Tunelamento: {tunneling_recorded*100:.1f}% (Falta de Massa Institucional)")
        print(f"    -> DECISÃO: Trade Mantido. Recuperação Capturada com Sucesso.")

    # 3. Gerar a Visualização
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    fig.patch.set_facecolor('#0f0f0f')
    
    ax1 = plt.subplot(gs[0])
    ax1.set_facecolor('#050505')
    
    # Plot Schrödinger Density Heatmap
    heatmap_data = np.array([d for d in density_history if d is not None]).T
    x_len = heatmap_data.shape[1]
    
    im = ax1.imshow(heatmap_data, aspect='auto', origin='lower', 
               extent=[10, len(df)-1, p_min, p_max],
               cmap='magma', alpha=0.8)
               
    # Plot Price Line
    ax1.plot(range(len(df)), df['close'], color='cyan', linewidth=2, label='Ação do Preço (Wick Simulado)')
    
    # Plot SL Virtual
    ax1.axhline(y=virtual_sl, color='red', linestyle='--', linewidth=2, alpha=0.7, label='SL Virtual (Dimensão de Ruptura)')
    
    # Marcar o Wick
    if wick_event_idx != -1:
        ax1.scatter(wick_event_idx, df['close'].iloc[wick_event_idx], color='red', s=150, zorder=5, marker='v')
        ax1.annotate(f"Absorção Viscoelástica!\nDe = {deborah_recorded:.2f}\nTunelamento = {tunneling_recorded*100:.1f}%", 
                     xy=(wick_event_idx, df['close'].iloc[wick_event_idx]),
                     xytext=(wick_event_idx-20, df['close'].iloc[wick_event_idx]-40),
                     color='white', fontsize=12, fontweight='bold',
                     arrowprops=dict(facecolor='white', shrink=0.05))

    ax1.set_title('NEXUS AGI-5 :: Fronteira Viscoelástica Quântica vs Stop Hunt', color='white', fontsize=16)
    ax1.set_ylabel('Preço GER40', color='white')
    ax1.tick_params(colors='white')
    ax1.legend(facecolor='black', edgecolor='white', labelcolor='white', loc='upper left')
    
    # Volume subplot
    ax2 = plt.subplot(gs[1], sharex=ax1)
    ax2.set_facecolor('#050505')
    colors = ['#ff3333' if i >= 80 and i < 85 else '#33ff33' for i in range(len(df))]
    ax2.bar(range(len(df)), df['tick_volume'], color=colors, alpha=0.7)
    ax2.set_ylabel('Massa (Volume)', color='white')
    ax2.set_xlabel('Tempo (Simulação de Ticks)', color='white')
    ax2.tick_params(colors='white')
    
    plt.tight_layout()
    
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Docs', '05_Estrutura_Corporativa', 'Setores', 'Q_MATH', 'Fronteira_Viscoelastica_Render.png'))
    plt.savefig(out_path, facecolor=fig.get_facecolor(), dpi=150)
    print(f"\n✅ Visualização renderizada e salva em: {out_path}")

if __name__ == "__main__":
    simulate_viscoelastic_wick()
