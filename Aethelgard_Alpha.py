from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.memory_core import NeuralMemoryCore
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
import time
import pandas as pd
import MetaTrader5 as mt5
from flask import Flask
import threading
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
nexus_data_str = "0;0;INIT;0;0;0;0;0"

@app.route('/nexus')
def get_nexus():
    return nexus_data_str

def run_server():
    app.run(host='127.0.0.1', port=5000)

class AethelgardAGI:
    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol
        self.bridge = MT5NeuralBridge(symbol)
        self.q_logic = QuantumIndicators()
        self.alchemist = MSNRAlchemist()
        self.oracle = QuantumOracle(simulations=5000)
        self.is_running = False
        self.regimes_cache = []
        self.signals_cache = []
        self.last_time = 0

    def startup(self):
        print(f"--- INICIANDO MOTOR v64 [PURE EXTREMITY SNIPER] :: {self.symbol} ---")
        threading.Thread(target=run_server, daemon=True).start()
        if not self.bridge.initialize(): return False
        self.bridge.fetch_full_history(count=5000)
        self.is_running = True
        return True

    def live_evolution_loop(self):
        global nexus_data_str
        window_calc = 200
        prev_s = 0
        prev_c = 0
        
        try:
            while self.is_running:
                rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 1000)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    
                    if not self.regimes_cache:
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Sincronizando v66 [ARS SNIPER]...")
                        for i in range(len(df)):
                            if i < window_calc:
                                self.regimes_cache.append("0|0")
                                self.signals_cache.append("0")
                                continue
                            
                            slice_df = df.iloc[i-window_calc:i+1]
                            r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                            self.regimes_cache.append(f"{r_score}|{conf}")
                            
                            # --- PROTOCOLO SGP v73 (Gênese Inteligente) ---
                            sig = 0
                            if r_score != 0:
                                is_genesis = (prev_s != r_score)
                                is_sovereign = self.alchemist.validate_sovereign_signal(slice_df, r_score, is_genesis)
                                
                                recent = [int(s) for s in self.signals_cache[-15:]]
                                is_locked = any(s != 0 for s in recent)

                                if is_sovereign and not is_locked:
                                    sig = r_score
                            
                            self.signals_cache.append(str(sig))
                            prev_s, prev_c = r_score, conf
                            
                        self.last_time = df.iloc[-1]['time']
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot v73 Concluído.")
                        
                        # EXPORTAÇÃO DE SNAPSHOT PARA BACKTEST v99
                        snapshot = df.copy()
                        snapshot['regime_signal'] = self.signals_cache
                        snapshot.to_parquet("Data/signals_snapshot.parquet")
                        print(f"--- SNAPSHOT DE SINAIS EXPORTADO PARA BACKTEST 1:1 ---")
                    
                    else:
                        new_rates = df[df['time'] > self.last_time]
                        if not new_rates.empty:
                            for idx in new_rates.index:
                                slice_df = df.loc[idx-window_calc:idx]
                                r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                                self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score}|{conf}")
                                
                                # --- PROTOCOLO SGP v73 (Live Execution) ---
                                sig = 0
                                if r_score != 0:
                                    is_genesis = (prev_s != r_score)
                                    is_sovereign = self.alchemist.validate_sovereign_signal(slice_df, r_score, is_genesis)
                                    
                                    is_mature = (conf > 50)
                                    recent_window = 10 if is_genesis else (15 if is_mature else 30)
                                    
                                    recent = [int(s) for s in self.signals_cache[-recent_window:]]
                                    is_locked = any(s != 0 for s in recent)
                                    
                                    if is_sovereign and not is_locked:
                                        sig = r_score



                                self.signals_cache.pop(0); self.signals_cache.append(str(sig))
                                prev_s, prev_c = r_score, conf
                                self.last_time = df.loc[idx, 'time']
                                if sig != 0: 
                                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] !!! ARS SINGULARIDADE CAPTURADA: [{sig}] !!!")
                                    print(f" > Alvo: External Range Liquidity (Top/Bottom Major).")

                    nexus_data_str = f"0;0;v66_ARS;{self.signals_cache[-1]};{','.join(self.regimes_cache)};0.00;1.0;{','.join(self.signals_cache)}"



                time.sleep(1)
        except Exception as e:
            print(f"ERRO: {e}")
            self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.bridge.shutdown()
        print("SISTEMA OFFLINE.")

if __name__ == "__main__":
    bot = AethelgardAGI("BTCUSD")
    if bot.startup():
        bot.live_evolution_loop()
