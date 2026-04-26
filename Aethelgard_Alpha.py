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
        print(f"--- RESTAURANDO MOTOR ESTÁVEL [v51 RESTORED] :: {self.symbol} ---")
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
                # Retorno ao Timeframe Único (M1) Estável
                rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 1000)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    
                    # Inicialização do Cache com Persistência de Estado (Garante caixas sólidas)
                    if not self.regimes_cache:
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Re-sincronizando Detector de Regime...")
                        for i in range(len(df)):
                            if i < window_calc:
                                self.regimes_cache.append("0|0")
                                self.signals_cache.append("0")
                                continue
                            
                            slice_df = df.iloc[i-window_calc:i+1]
                            r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                            self.regimes_cache.append(f"{r_score}|{conf}")
                            
                            # Lógica de Sinais v51 (Equilibrium/Sniper) - Otimizada para o passado
                            sig = 0
                            self.signals_cache.append(str(sig))
                            
                            # CRÍTICO: Atualiza estado para o próximo candle do histórico
                            prev_s, prev_c = r_score, conf
                            
                        self.last_time = df.iloc[-1]['time']
                    
                    # Processamento Live Estável
                    else:
                        new_rates = df[df['time'] > self.last_time]
                        if not new_rates.empty:
                            for idx in new_rates.index:
                                slice_df = df.loc[idx-window_calc:idx]
                                r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                                
                                self.regimes_cache.pop(0)
                                self.regimes_cache.append(f"{r_score}|{conf}")
                                
                                # Gatilho Sniper v51 (Equilíbrio Matrix)
                                sig = 0
                                if r_score != 0:
                                    current_price = slice_df['close'].iloc[-1]
                                    volatility = slice_df['close'].pct_change().std()
                                    if pd.isna(volatility) or volatility == 0: volatility = 0.0001
                                    
                                    # Range de 50 candles para Equilibrium
                                    lookback_range = slice_df.iloc[-50:]
                                    r_high = lookback_range['high'].max()
                                    r_low = lookback_range['low'].min()
                                    equilibrium = (r_high + r_low) / 2
                                    
                                    if r_score == 1: # BULL (Apenas no Desconto)
                                        if current_price < equilibrium:
                                            prob = self.oracle.run_monte_carlo(current_price, volatility, current_price*1.002, current_price*0.998, steps=50)
                                            if prob > 0.60: sig = 1
                                    elif r_score == 2: # BEAR (Apenas no Premium)
                                        if current_price > equilibrium:
                                            prob = self.oracle.run_monte_carlo(current_price, volatility, current_price*0.998, current_price*1.002, steps=50)
                                            if prob > 0.60: sig = 2

                                self.signals_cache.pop(0)
                                self.signals_cache.append(str(sig))
                                
                                prev_s, prev_c = r_score, conf
                                self.last_time = df.loc[idx, 'time']
                                print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Live: Regime={r_score} | Sinal={sig}")

                    nexus_data_str = f"0;0;STABLE_v51;{self.signals_cache[-1]};{','.join(self.regimes_cache)};0.00;1.0;{','.join(self.signals_cache)}"

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
