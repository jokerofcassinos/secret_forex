from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
from Code.N_Core.quantum_clouds import QuantumCloudTracker
from Code.N_Core.fluid_dynamics import LBMFluidDynamics
from Code.N_Core.plasma_market import PlasmaMarketTracker
from Code.N_Core.random_matrix import RandomMatrixTracker
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
        self.cloud_tracker = None
        self.lbm_tracker = None
        self.plasma_tracker = None
        self.rmt_tracker = None
        self.plasma_zones = None
        self.is_running = False
        self.regimes_cache = []
        self.signals_cache = []
        self.dots_cache = []
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
                    
                    # Inicialização do Quantum Cloud Tracker dinâmico
                    if self.cloud_tracker is None:
                        p_min = df['low'].min() - 100
                        p_max = df['high'].max() + 100
                        self.cloud_tracker = QuantumCloudTracker(price_min=p_min, price_max=p_max, bins=50) # 50 bins para MT5
                        self.cloud_tracker.initialize_wave(df['close'].iloc[0], sigma=(self.cloud_tracker.dx * 10))

                    # Inicialização do LBM Fluid Dynamics Tracker
                    if self.lbm_tracker is None:
                        p_min = df['low'].min() - 100
                        p_max = df['high'].max() + 100
                        self.lbm_tracker = LBMFluidDynamics(price_min=p_min, price_max=p_max, bins=50, tau=0.8)

                    # Inicialização do MHD Plasma Market (Z-Pinch)
                    if self.plasma_tracker is None:
                        self.plasma_tracker = PlasmaMarketTracker()
                        self.plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df, lookback=200)

                    # Inicialização do RMT Spectral Filter
                    if self.rmt_tracker is None:
                        self.rmt_tracker = RandomMatrixTracker(time_steps=100)

                    if not self.regimes_cache:
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Sincronizando v66 [ARS SNIPER]...")
                        
                        scores_hist = []
                        for i in range(len(df)):
                            if i < window_calc:
                                self.regimes_cache.append("0|0")
                                self.signals_cache.append("0")
                                scores_hist.append(0)
                                continue
                            
                            slice_df = df.iloc[i-window_calc:i+1]
                            r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                            self.regimes_cache.append(f"{r_score}|{conf}")
                            scores_hist.append(r_score)
                            
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
                        
                        self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df, scores_hist)]
                        self.last_time = df.iloc[-1]['time']
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot v73 Concluído.")
                    
                    else:
                        # --- PROCESSO DE TICKS EM TEMPO REAL v410 ---
                        slice_df = df.iloc[-window_calc:]
                        r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                        
                        is_genesis = (prev_s != r_score)
                        if is_genesis: self.genesis_count = 0
                        
                        is_sovereign = self.alchemist.validate_sovereign_signal(slice_df, r_score, is_genesis or (self.genesis_count < 3))
                        
                        # Processa a Malha Quântica (Lado Python -> C++)
                        density_schrod = self.cloud_tracker.step(slice_df, dt=1.0)
                        cloud_str = ""
                        if density_schrod is not None:
                            cloud_arr = []
                            for i, d in enumerate(density_schrod):
                                p = self.cloud_tracker.index_to_price(i)
                                cloud_arr.append(f"{p:.2f}|{d:.4f}")
                            cloud_str = ",".join(cloud_arr)

                        # Processa LBM Dynamics
                        lbm_signal = "LAMINAR_FLOW"
                        lbm_density, lbm_velocity = self.lbm_tracker.process_tick_stream(slice_df.tail(10), steps=5)
                        if lbm_density is not None and lbm_velocity is not None:
                            lbm_signal = self.lbm_tracker.detect_squeeze_rupture(df['close'].iloc[-1], lbm_density, lbm_velocity)

                        # Processa MHD Plasma Z-Pinch
                        z_pinch_signal = "NEUTRAL"
                        curr_candle = df.iloc[-1]
                        prev_candle = df.iloc[-2]
                        
                        if self.genesis_count % 100 == 0:
                             self.plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df, lookback=200)

                        z_idx, z_type = self.plasma_tracker.process_tick(curr_candle, prev_candle, self.plasma_zones)
                        if z_idx > 90.0:
                            z_pinch_signal = f"Z_PINCH_{z_type}"

                        # Processa RMT Spectral Filter
                        rmt_signal = "NOISE"
                        _, power_ratio, is_pure = self.rmt_tracker.process_spectral_filter(df)
                        if is_pure:
                            rmt_signal = f"PURE_SIGNAL_x{power_ratio:.1f}"

                        # Determina o Status Visual Instantâneo
                        if r_score == 1:
                            status_txt = "BULL_PREVISAO" if not is_sovereign else "TSUNAMI_BULL_ATIVO"
                        elif r_score == 2:
                            status_txt = "BEAR_PREVISAO" if not is_sovereign else "TSUNAMI_BEAR_ATIVO"
                        else:
                            status_txt = "AGUARDANDO_IGNICAO"
                            
                        # Modificadores de Status Quântico
                        if lbm_signal == "FLUID_RUPTURE_BULL":
                            status_txt += " | [SQUEEZE LBM BULL]"
                        elif lbm_signal == "FLUID_RUPTURE_BEAR":
                            status_txt += " | [SQUEEZE LBM BEAR]"
                            
                        if z_pinch_signal != "NEUTRAL":
                            status_txt += f" | [⚠️ Z-PINCH: {z_type}]"
                            
                        if rmt_signal != "NOISE":
                            status_txt += f" | [RMT PURE]"

                        # Estado em tempo real para o MT5
                        rt_regime = f"{r_score if is_sovereign else 0}|{conf}"
                        
                        # --- DEFESA CO-PILOTO EM TEMPO REAL (v410) ---
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
                            
                            if body > (atr * 1.5) or is_genesis:
                                sig = 1 if r_score == 1 else 2
                                print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 👁️ NEXUS AWARE: {status_txt}")
                                
                            # Atualização Síncrona
                            self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score if is_sovereign else 0}|{conf}")
                            self.signals_cache.pop(0); self.signals_cache.append(str(sig))
                            
                            # Re-calcula dots para todo o DF
                            scores_list = [int(r.split('|')[0]) for r in self.regimes_cache]
                            self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df.tail(len(self.regimes_cache)), scores_list)]
                            
                            prev_s, prev_c = r_score, conf
                            self.last_time = df.iloc[-1]['time']
                        
                        # Preço Médio Institucional (EMA 89)
                        inst_avg = df['close'].ewm(span=89, adjust=False).mean().iloc[-1]
                        # Saúde do Regime (v27.0)
                        health = self.q_logic.calculate_regime_health(df)
                        status_final = f"{status_txt} | SAÚDE: {health}%"
                        
                        display_regimes = self.regimes_cache[1:] + [rt_regime]
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal}"

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
