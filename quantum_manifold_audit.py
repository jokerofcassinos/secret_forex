"""
🌌 NEXUS :: QUANTUM MANIFOLD AUDIT (QMA) v1.0
Filtro Microscópico de Tensores e Validação de Monólito.

Este script realiza uma auditoria profunda vela-por-vela do motor Aethelgard,
extraindo todos os parâmetros internos de decisão para eliminar o flicker e lag.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path para importações
sys.path.append(os.getcwd())

from Code.N_Core.quantum_indicators import QuantumIndicators

def run_audit(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_H1, n_bars=300):
    print(f"🔬 QMA :: Iniciando Auditoria Microscópica para {symbol}...")
    
    if not mt5.initialize():
        print("❌ QMA :: Falha ao inicializar MetaTrader 5.")
        return
    
    # 1. Fetch de Dados Reais
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars + 200)
    if bars is None or len(bars) == 0:
        print("❌ QMA :: Falha ao obter dados do MT5.")
        return
    
    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 2. Setup do Motor
    qi = QuantumIndicators()
    audit_data = []
    
    prev_s, prev_c = 0, 0
    
    print(f"🌀 QMA :: Processando {n_bars} velas com Inércia Zero v16.0...")
    
    # Loop de Auditoria
    for i in range(200, len(df)):
        slice_df = df.iloc[:i+1]
        
        # --- PTI MOCKING (v17.0 Audit Resilience) ---
        # Simula a instabilidade quântica baseada no momentum e ATR
        recent = slice_df.tail(5)
        momentum = abs(recent['close'].iloc[-1] - recent['close'].iloc[0])
        local_atr = (slice_df['high'] - slice_df['low']).rolling(14).mean().iloc[-1]
        
        # PTI Mock: escala momentum em relação ao ATR. 
        # Valores > 0.8 indicam instabilidade (exaustão).
        pti_mock = min(1.0, momentum / (local_atr * 3.0 + 1e-9))
        
        q_math_data = {
            "ricci_curvature": pti_mock * 10.0, # Ricci cresce com instabilidade
            "h_entropy": pti_mock * 5.0,
            "rmt_signal": f"NOISE_x{max(0.1, 4.0 - pti_mock*4):.1f}", # Power ratio cai com instabilidade
            "ksi_val": max(0.0, 1.0 - pti_mock),
            "is_collapsed": pti_mock > 0.9,
            "status": "ACTIVE"
        }

        # Simula o cálculo de regime com DEBUG ativado
        r_score, r_conf, debug = qi.advanced_regime_score(
            slice_df.tail(200), 
            prev_s, 
            prev_c, 
            q_math_data=q_math_data,
            debug=True
        )
        
        # Captura telemetria
        row = {
            "time": df.iloc[i]['time'],
            "close": df.iloc[i]['close'],
            "score": r_score,
            "conf": r_conf,
            "pti": debug.get("pti", 0),
            "qdd_dir": debug.get("qdd_dir", 0),
            "qdd_conf": 1 if debug.get("qdd_confirmed") else 0,
            "gravity_block_bull": 1 if debug.get("gravity_bull_block") else 0,
            "gravity_block_bear": 1 if debug.get("gravity_bear_block") else 0,
            "wick_bull": 1 if debug.get("wick_bull") else 0,
            "wick_bear": 1 if debug.get("wick_bear") else 0,
            "ema_trend": debug.get("ema_trend"),
            "ema_macro": debug.get("ema_macro"),
            "ema_gravity": debug.get("ema_gravity"),
            "atr": debug.get("atr"),
            "last_polar": debug.get("last_polar"),
            "bars_neutral": debug.get("bars_neutral")
        }
        audit_data.append(row)
        
        prev_s, prev_c = r_score, r_conf
    
    audit_df = pd.DataFrame(audit_data)
    
    # 3. Exportação de Relatório Tabular (CSV)
    csv_path = "artifacts/manifold_audit_report.csv"
    os.makedirs("artifacts", exist_ok=True)
    audit_df.to_csv(csv_path, index=False)
    print(f"✅ QMA :: Relatório CSV gerado em: {csv_path}")
    
    # 4. Visualização de Laboratório (Matplotlib HD)
    plt.figure(figsize=(16, 10))
    
    # Subplot 1: Preço e Regimes
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(audit_df['time'], audit_df['close'], color='gray', alpha=0.6, label='Preço')
    ax1.plot(audit_df['time'], audit_df['ema_trend'], '--', color='cyan', alpha=0.4, label='EMA 34')
    ax1.plot(audit_df['time'], audit_df['ema_macro'], '--', color='magenta', alpha=0.4, label='EMA 89')
    ax1.plot(audit_df['time'], audit_df['ema_gravity'], '-', color='blue', alpha=0.3, label='EMA 200')
    
    # Desenha boxes de regime
    for i in range(1, len(audit_df)):
        if audit_df['score'].iloc[i] == 1:
            ax1.axvspan(audit_df['time'].iloc[i-1], audit_df['time'].iloc[i], color='teal', alpha=0.2)
        elif audit_df['score'].iloc[i] == 2:
            ax1.axvspan(audit_df['time'].iloc[i-1], audit_df['time'].iloc[i], color='red', alpha=0.2)
            
    ax1.set_title(f"QMA :: Visualização de Variedade - {symbol}")
    ax1.legend()
    ax1.grid(alpha=0.1)
    
    # Subplot 2: Tensores de Decisão (PTI e QDD)
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.plot(audit_df['time'], audit_df['pti'], color='orange', label='PTI (Phase Transition)')
    ax2.step(audit_df['time'], audit_df['qdd_dir'] / 2.0, color='lime', alpha=0.5, label='QDD Direction (scaled)')
    ax2.axhline(0.90, color='red', linestyle=':', alpha=0.5, label='Exhaustion Threshold')
    
    # Marcação de bloqueios
    blocks = audit_df[audit_df['gravity_block_bull'] == 1]
    if not blocks.empty:
        ax2.scatter(blocks['time'], [0.1]*len(blocks), marker='x', color='blue', label='Gravity Block active')
        
    ax2.set_title("Tensores Microscópicos (PTI / QDD / Blocks)")
    ax2.legend()
    ax2.grid(alpha=0.1)
    
    plt.tight_layout()
    img_path = "artifacts/manifold_visual_audit.png"
    plt.savefig(img_path, dpi=200)
    print(f"🖼️ QMA :: Holograma visual gerado em: {img_path}")
    
    # 5. Resumo Executivo das últimas 10 velas
    print("\n📋 RESUMO MICROSCÓPICO (Últimas 10 Velas):")
    print(audit_df[['time', 'close', 'score', 'conf', 'pti', 'qdd_dir', 'last_polar', 'bars_neutral']].tail(10).to_string(index=False))

    mt5.shutdown()

if __name__ == "__main__":
    asset = "BTCUSD"
    if len(sys.argv) > 1: asset = sys.argv[1]
    run_audit(symbol=asset)
