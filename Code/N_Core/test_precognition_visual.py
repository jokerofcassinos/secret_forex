import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import time
import MetaTrader5 as mt5

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', '..'))

from Code.N_Core.quantum_projection import QuantumPreCognitionNode

def run_real_audit():
    print("[AUDIT] CONECTANDO AO METATRADER 5...")
    if not mt5.initialize():
        print("❌ Falha ao inicializar MT5")
        return

    symbol = "GER40.cash"
    print(f"[AUDIT] EXTRAINDO DADOS REAIS DE {symbol}...")
    
    # Extrai as últimas 300 barras para análise de plasma
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 300)
    if rates is None or len(rates) == 0:
        print("❌ Falha ao extrair dados")
        mt5.shutdown()
        return
        
    df = pd.DataFrame(rates)
    current_price = df['close'].iloc[-1]
    
    # Calcula ATR real para a simulação
    df['tr'] = np.maximum(df['high'] - df['low'], 
                np.maximum(abs(df['high'] - df['close'].shift(1)), 
                           abs(df['low'] - df['close'].shift(1))))
    atr = df['tr'].tail(14).mean()
    
    print(f"[AUDIT] Preço Atual: {current_price} | ATR: {atr:.2f}")

    # 1. INICIALIZA O NÓ DE PRE-COGNITION
    node = QuantumPreCognitionNode(symbol=symbol)
    
    # 2. CALCULA ZONAS DE PLASMA REAIS
    # O nó usa o PlasmaMarketTracker internamente
    zones = node.mhd_simulator.scan_for_plasma_zones(df)
    print(f"[AUDIT] Plasma Top: {zones['top_level']:.2f} (Density: {zones['top_density']:.1f})")
    print(f"[AUDIT] Plasma Bottom: {zones['bottom_level']:.2f} (Density: {zones['bottom_density']:.1f})")

    # 3. EXECUTA A PROJEÇÃO C++ (MONTE CARLO DE ALTA VELOCIDADE)
    start_time = time.time()
    res = node.project_containment_horizon(df, current_price, atr)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"[OK] Projecao C++ concluida em {elapsed:.2f}ms")
    
    # 4. RENDERIZAÇÃO VISUAL PROFISSIONAL
    plt.figure(figsize=(14, 8))
    plt.style.use('dark_background')
    
    # Plot do Histórico Recente
    plt.plot(df['close'].tail(50).values, color='gray', alpha=0.5, label='Histórico (M5)')
    
    # Horizonte de Futuro (Projection)
    future_x = np.arange(50, 90) # 40 passos no futuro
    
    # Linhas de Plasma
    plt.axhline(y=zones['top_level'], color='cyan', linestyle=':', alpha=0.6, label='Plasma Horizon (Top)')
    plt.axhline(y=zones['bottom_level'], color='purple', linestyle=':', alpha=0.6, label='Plasma Horizon (Bottom)')
    
    # Stop Loss de Singularidade
    plt.axhline(y=res['sl_bull_singular'], color='#00ffcc', linewidth=2.5, label='SL SINGULARITY (BULL)')
    plt.axhline(y=res['sl_bear_singular'], color='#ff3366', linewidth=2.5, label='SL SINGULARITY (BEAR)')
    
    # Zona de Contenção
    plt.fill_between(future_x, res['sl_bull_singular'], res['sl_bear_singular'], color='cyan', alpha=0.1, label='Magnetic Containment')
    
    plt.title(f"NEXUS :: QUANTUM PRE-COGNITION REAL-TIME AUDIT ({symbol})\nBreach Prob: {res['breach_prob']*100:.2f}% | Latency: {elapsed:.2f}ms", fontsize=12, pad=20)
    plt.ylabel("Price")
    plt.xlabel("Relative Ticks (Historical -> Future Projection)")
    plt.legend(loc='upper left', frameon=True, facecolor='#121212')
    plt.grid(alpha=0.05)
    
    save_path = os.path.join(current_dir, "PreCognition_RealData_Audit.png")
    plt.savefig(save_path, dpi=120)
    print(f"📊 Auditoria REAL salva em: {save_path}")
    
    mt5.shutdown()
    plt.show()

if __name__ == "__main__":
    run_real_audit()
