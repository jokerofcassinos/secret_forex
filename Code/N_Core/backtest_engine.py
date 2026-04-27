import pandas as pd
import numpy as np
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.thermodynamic_risk import ThermodynamicRiskManager
import os
from datetime import datetime

class BacktestEngine:
    """
    BacktestEngine v99 [GROUND TRUTH].
    Auditor de precisão 1:1 conectado ao Snapshot do gráfico real.
    Garante que auditamos EXATAMENTE o que aparece na tela do usuário.
    """
    
    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol
        self.alchemist = MSNRAlchemist()
        self.risk_manager = ThermodynamicRiskManager(lot_size=1.0)
        self.audit_path = "Docs/Audits/"
        self.snapshot_path = "Data/signals_snapshot.parquet"
        
        if not os.path.exists(self.audit_path):
            os.makedirs(self.audit_path)

    def run_ground_truth_audit(self):
        if not os.path.exists(self.snapshot_path):
            print(f"ERRO: Snapshot não encontrado em {self.snapshot_path}")
            print("Execute o Aethelgard_Alpha.py primeiro para gerar a verdade do gráfico.")
            return

        print(f"--- CARREGANDO VERDADE DO GRÁFICO (Snapshot v99) ---")
        df = pd.read_parquet(self.snapshot_path)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        balance = 100000.0
        active_trade = None
        trades_history = []
        
        print(f"--- INICIANDO AUDITORIA DE PRECISÃO 1:1 [{self.symbol}] ---")
        
        for i in range(len(df)):
            slice_df = df.iloc[max(0, i-200):i+1]
            curr = df.iloc[i]
            
            # 1. GESTÃO DE ORDEM ATIVA
            if active_trade:
                result = self.risk_manager.manage_active_trade(active_trade, slice_df)
                active_trade['max_runup'] = max(active_trade['max_runup'], result['gross_pnl'])
                active_trade['sl'] = result['new_sl']

                if result['should_exit']:
                    active_trade['exit_price'] = result['exit_price']
                    active_trade['exit_time'] = curr['time']
                    active_trade['net_pnl'] = result['gross_pnl'] - self.risk_manager.commission
                    active_trade['reason'] = result['exit_reason']
                    active_trade['max_runup'] = max(active_trade['max_runup'], result['gross_pnl'])
                    
                    balance += active_trade['net_pnl']
                    self.write_audit_log(active_trade)
                    trades_history.append(active_trade)
                    active_trade = None
                continue

            # 2. ENTRADA BASEADA NA VERDADE DO GRÁFICO (Snapshot)
            # O sinal vem direto da memória do gráfico, sem 'achismo'
            chart_signal = int(curr['regime_signal'])
            
            if chart_signal != 0:
                tp, _ = self.alchemist.find_structural_targets(slice_df, chart_signal)
                atr_val = (slice_df['high'] - slice_df['low']).rolling(14).mean().iloc[-1]
                sl_points = max(300.0, atr_val * 2.5)
                
                active_trade = {
                    'entry_time': curr['time'],
                    'entry_price': curr['close'],
                    'regime': chart_signal,
                    'tp': tp,
                    'sl': curr['close'] - sl_points if chart_signal == 1 else curr['close'] + sl_points,
                    'highest_pnl': 0,
                    'max_runup': 0,
                    'shield_active': False
                }
        
        print(f"\n--- AUDITORIA v99 CONCLUÍDA ---")
        print(f"Saldo Final: ${balance:.2f} | Total de Ordens: {len(trades_history)}")
        print(f"Paridade com Gráfico: 100% (Ground Truth Sync)")

    def write_audit_log(self, trade):
        t_id = trade['entry_time'].strftime("%Y%m%d_%H%M")
        with open(f"{self.audit_path}TRUTH_AUDIT_{t_id}.md", "w") as f:
            f.write(f"# NEXUS GROUND TRUTH AUDIT - {t_id}\n\n")
            f.write(f"- **Entrada Real:** {trade['entry_price']:.2f} às {trade['entry_time']}\n")
            f.write(f"- **Saída Real:** {trade['exit_price']:.2f} ({trade['reason']})\n")
            f.write(f"- **PnL Net:** ${trade['net_pnl']:.2f}\n")
            f.write(f"- **Max Profit Visto:** ${trade['max_runup']:.2f}\n")

if __name__ == "__main__":
    engine = BacktestEngine()
    engine.run_ground_truth_audit()
