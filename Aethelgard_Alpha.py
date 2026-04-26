from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.memory_core import NeuralMemoryCore
from Code.N_Core.quantum_indicators import QuantumIndicators
import time
import pandas as pd
import MetaTrader5 as mt5
from flask import Flask
import threading
import logging
import numpy as np

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
nexus_data_str = "0;0;INIT;0;0"

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
        self.is_running = False

    def startup(self):
        print(f"--- INICIANDO MOTOR DE SOBERANIA [SL-1] :: {self.symbol} ---")
        threading.Thread(target=run_server, daemon=True).start()
        if not self.bridge.initialize(): return False
        self.bridge.fetch_full_history(count=5000)
        self.is_running = True
        return True

    def live_evolution_loop(self):
        global nexus_data_str
        print("SISTEMA DE BLINDAGEM DE ESTADO ATIVO...")
        try:
            while self.is_running:
                rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 800)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    
                    regimes_hist = []
                    window_calc = 100 
                    
                    # MEMÓRIA DE ESTADO SOBERANA
                    prev_s = 0
                    prev_c = 0
                    
                    for i in range(len(df)):
                        if i < window_calc:
                            regimes_hist.append("0|0")
                            continue
                        
                        slice_df = df.iloc[i-window_calc:i+1]
                        r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                        regimes_hist.append(f"{r_score}|{conf}")
                        prev_s = r_score 
                        prev_c = conf
                    
                    # Telemetria
                    prices = df['close']
                    ema_200 = prices.ewm(span=200, adjust=False).mean().iloc[-1]
                    dist_ema = prices.iloc[-1] - ema_200
                    rsi_val = self.q_logic.calculate_rsi(prices).iloc[-1]
                    
                    current_regime = "SOVEREIGN_FLOW"
                    nexus_data_str = f"{rsi_val:.2f};{dist_ema:.2f};{current_regime};0;{','.join(regimes_hist)}"
                    
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Regime Sólido: Ok | Conf: {prev_c}%")

                time.sleep(1)
                
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.bridge.shutdown()
        print("SISTEMA OFFLINE.")

if __name__ == "__main__":
    bot = AethelgardAGI("BTCUSD")
    if bot.startup():
        bot.live_evolution_loop()
