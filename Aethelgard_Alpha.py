from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
import time
import pandas as pd
import numpy as np
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
    def __init__(self, symbol="GER40.cash"):
        self.symbol = symbol
        self.bridge = MT5NeuralBridge(symbol)
        self.q_logic = QuantumIndicators()
        self.alchemist = MSNRAlchemist()
        self.oracle = QuantumOracle(simulations=5000)
        self.is_running = False
        self.regimes_cache = []
        self.signals_cache = []
        self.last_time = 0
        self.genesis_count = 0

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
        status_txt = "INICIALIZANDO"
        
        try:
            while self.is_running:
                # Execução em H2 para análise de monólito macro
                rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H2, 0, 1000)
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
                            
                            # --- RADAR DE ANOMALIAS (HISTÓRICO) ---
                            sig = 0
                            if r_score != 0:
                                curr_h = slice_df.iloc[-1]
                                body_h = abs(curr_h['close'] - curr_h['open'])
                                
                                high_low_h = slice_df['high'] - slice_df['low']
                                high_close_h = np.abs(slice_df['high'] - slice_df['close'].shift(1))
                                low_close_h = np.abs(slice_df['low'] - slice_df['close'].shift(1))
                                ranges_h = pd.concat([high_low_h, high_close_h, low_close_h], axis=1)
                                true_range_h = np.max(ranges_h, axis=1)
                                atr_h = true_range_h.rolling(14).mean().iloc[-1]
                                
                                is_genesis_h = (prev_s != r_score)
                                if body_h > (atr_h * 1.5) or is_genesis_h:
                                    sig = 1 if r_score == 1 else 2
                            
                            self.signals_cache.append(str(sig))
                            prev_s, prev_c = r_score, conf
                            
                        self.last_time = df.iloc[-1]['time']
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot v73 Concluído.")
                    
                    else:
                        # --- PROCESSO DE TICKS EM TEMPO REAL v410 ---
                        slice_df = df.iloc[-window_calc:]
                        r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                        
                        is_genesis = (prev_s != r_score)
                        if is_genesis: self.genesis_count = 0
                        
                        is_sovereign = self.alchemist.validate_sovereign_signal(slice_df, r_score, is_genesis or (self.genesis_count < 3))
                        
                        # Determina o Status Visual Instantâneo
                        if r_score == 1:
                            status_txt = "BULL_PREVISAO" if not is_sovereign else "TSUNAMI_BULL_ATIVO"
                        elif r_score == 2:
                            status_txt = "BEAR_PREVISAO" if not is_sovereign else "TSUNAMI_BEAR_ATIVO"
                        else:
                            status_txt = "AGUARDANDO_IGNICAO"
                        
                        # Estado em tempo real para o MT5
                        rt_regime = f"{r_score if is_sovereign else 0}|{conf}"
                        
                        # --- DEFESA CO-PILOTO EM TEMPO REAL (v410) ---
                        # Escaneia e protege ordens a cada segundo (independente do fechamento do candle)
                        ema_trend = df['close'].ewm(span=34, adjust=False).mean().iloc[-1]
                        ema_macro = df['close'].ewm(span=89, adjust=False).mean().iloc[-1]
                        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
                        
                        if r_score != 0:
                            self.bridge.trailing_sl_tp(r_score, ema_trend, ema_macro, atr)
                        
                        # --- RADAR DE ANOMALIAS (PENSAMENTO ANALÍTICO) ---
                        sig = 0
                        new_rates = df[df['time'] > self.last_time]
                        if not new_rates.empty:
                            self.genesis_count += 1
                            curr = df.iloc[-1]
                            body = abs(curr['close'] - curr['open'])
                            
                            # Pensamento da IA: Houve injeção de massa crítica ou é o INÍCIO de um novo regime?
                            if body > (atr * 1.5) or is_genesis:
                                sig = 1 if r_score == 1 else 2
                                status_txt = f"ANOMALIA_INSTITUCIONAL_{'BULL' if sig == 1 else 'BEAR'}"
                                print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 👁️ NEXUS AWARE: {status_txt} (Massa: {body/atr:.1f}x ATR / Genesis: {is_genesis})")
                                
                            # --- ATUALIZAÇÃO SÍNCRONA DE CACHE ---
                            self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score if is_sovereign else 0}|{conf}")
                            self.signals_cache.pop(0); self.signals_cache.append(str(sig))
                            prev_s, prev_c = r_score, conf
                            self.last_time = df.iloc[-1]['time']
                        
                        # MONTAGEM DA STRING COM O PRESENTE REAL (Cache + RT)
                        display_regimes = self.regimes_cache[1:] + [rt_regime]
                        nexus_data_str = f"0;0;{status_txt};{self.signals_cache[-1]};{','.join(display_regimes)};0.00;1.0;{','.join(self.signals_cache)}"

                time.sleep(1)
        except Exception as e:
            print(f"ERRO: {e}")
            self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.bridge.shutdown()
        print("SISTEMA OFFLINE.")

if __name__ == "__main__":
    bot = AethelgardAGI("GER40.cash")
    if bot.startup():
        bot.live_evolution_loop()
