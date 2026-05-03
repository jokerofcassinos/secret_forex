from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
from Code.N_Core.quantum_clouds import QuantumCloudTracker
from Code.N_Core.fluid_dynamics import LBMFluidDynamics
from Code.N_Core.plasma_market import PlasmaMarketTracker
from Code.N_Core.random_matrix import RandomMatrixTracker
from Code.N_Core.quantum_walk import QRWTracker
from Code.N_Core.yield_governor import YieldGovernor
import time
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from flask import Flask, request
import threading
import logging
import sys

# Windows UTF-8 console fix
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
nexus_data_str = "0;0;INIT;0;0;0;0;0"
current_mt5_tf = mt5.TIMEFRAME_H2 # Global de timeframe dinâmico

@app.route('/nexus')
def get_nexus():
    global current_mt5_tf
    # Captura o timeframe enviado pelo indicador MQL5 (?tf=...)
    tf_val = request.args.get('tf')
    if tf_val:
        try:
            current_mt5_tf = int(tf_val)
        except ValueError: pass
    return nexus_data_str

def run_server():
    app.run(host='127.0.0.1', port=5000)

class AethelgardAGI:
    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol
        self.bridge = MT5NeuralBridge(symbol)
        self.q_logic = QuantumIndicators()
        
        # --- VERIFICAÇÃO RG-QDD ---
        from Code.N_Core.quantum_indicators import QDD_AVAILABLE
        self.qdd_active = QDD_AVAILABLE
        if self.qdd_active:
            print("💎 NEXUS AGI :: RG-QDD ENGINE [ACTIVE] :: Quantum Purification Gate Operational.")
        else:
            print("⚠️ NEXUS AGI :: RG-QDD ENGINE [OFFLINE] :: Falling back to standard TQFM logic.")
        self.alchemist = MSNRAlchemist()
        self.oracle = QuantumOracle(simulations=5000)
        self.yield_governor = YieldGovernor(danger_window=30, danger_threshold=25.0)
        self.cloud_tracker = None
        self.lbm_tracker = None
        self.plasma_tracker = None
        self.rmt_tracker = None
        self.qrw_tracker = None
        self.plasma_zones = None
        self.is_running = False
        self.regimes_cache = []
        self.signals_cache = []
        self.lbm_cache = []
        self.z_pinch_cache = []
        self.qrw_cache = []
        self.dots_cache = []
        self.sec_cache = []
        self.last_time = 0
        self.genesis_count = 0
        self.last_sec_state = False # State tracker para logs SEC

    def startup(self):
        print(f"--- INICIANDO MOTOR v64 [PURE EXTREMITY SNIPER] :: {self.symbol} ---")
        threading.Thread(target=run_server, daemon=True).start()
        if not self.bridge.initialize(): return False
        self.bridge.fetch_full_history(count=5000)
        self.is_running = True
        return True

    def live_evolution_loop(self):
        global nexus_data_str, current_mt5_tf
        window_calc = 200
        prev_s = 0
        prev_c = 0
        is_sovereign = False
        status_txt = "INICIALIZANDO"

        try:
            current_processed_tf = None
            while self.is_running:
                # --- DINAMISMO TEMPORAL NEXUS v2 (MQL5-PUSH) ---
                selected_tf = current_mt5_tf
                
                # Se o timeframe mudou, limpa o cache para forçar recálculo completo
                if current_processed_tf is not None and selected_tf != current_processed_tf:
                    print(f"🔄 TIME-SHIFT DETECTADO: Recalculando malha neural para o novo timeframe.")
                    self.regimes_cache = []
                    self.signals_cache = []
                    self.lbm_cache = []
                    self.z_pinch_cache = []
                    self.qrw_cache = []
                    self.dots_cache = []
                    self.cloud_tracker = None
                    self.lbm_tracker = None
                    self.plasma_tracker = None
                    self.rmt_tracker = None
                    self.qrw_tracker = None
                    prev_s = 0
                    prev_c = 0
                    is_sovereign = False

                current_processed_tf = selected_tf

                rates = mt5.copy_rates_from_pos(self.symbol, selected_tf, 0, 1000)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)

                    # Nome amigável do TF para o log
                    tf_name = "M15" if selected_tf == mt5.TIMEFRAME_M15 else str(selected_tf)
                    
                    # Inicializações Quânticas
                    if self.cloud_tracker is None:
                        p_min = df['low'].min() - 100
                        p_max = df['high'].max() + 100
                        self.cloud_tracker = QuantumCloudTracker(price_min=p_min, price_max=p_max, bins=512)
                        self.cloud_tracker.initialize_wave(df['close'].iloc[-1], sigma=(self.cloud_tracker.dx * 15))

                    if self.lbm_tracker is None:
                        p_min = df['low'].min() - 100
                        p_max = df['high'].max() + 100
                        self.lbm_tracker = LBMFluidDynamics(price_min=p_min, price_max=p_max, bins=200, tau=1.0)

                    if self.plasma_tracker is None:
                        self.plasma_tracker = PlasmaMarketTracker()
                        self.plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df, lookback=200)

                    if self.rmt_tracker is None:
                        self.rmt_tracker = RandomMatrixTracker(time_steps=100)
                        
                    if self.qrw_tracker is None:
                        self.qrw_tracker = QRWTracker(positions=201)

                    if not self.regimes_cache:
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Sincronizando v74 [TOPOLOGICAL BLACKOUT]...")
                        
                        # CALCULA EMAs E ATR GLOBALMENTE PARA EVITAR INSTABILIDADE E LENTIDÃO
                        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
                        df['ema_mid'] = df['close'].ewm(span=21, adjust=False).mean()
                        df['ema_trend'] = df['close'].ewm(span=34, adjust=False).mean()
                        df['ema_macro'] = df['close'].ewm(span=89, adjust=False).mean()
                        df['ema_gravity'] = df['close'].ewm(span=200, adjust=False).mean()
                        
                        # ATR Calculation for Anomaly Detection
                        high_low = df['high'] - df['low']
                        high_close = np.abs(df['high'] - df['close'].shift(1))
                        low_close = np.abs(df['low'] - df['close'].shift(1))
                        tr_full = np.maximum(high_low, np.maximum(high_close, low_close))
                        df['atr_static'] = tr_full.rolling(14).mean()

                        # --- ANÁLISE CALABI-YAU HISTÓRICA (PURGA DE SINAIS) ---
                        t_open = df['open'].values
                        t_high = df['high'].values
                        t_low = df['low'].values
                        t_close = df['close'].values
                        t_vol = df['tick_volume'].values if 'tick_volume' in df.columns else np.zeros(len(df))
                        t_hl = (df['high'] - df['low']).values
                        t_ret = df['close'].pct_change().fillna(0).values
                        raw_data_10d = np.vstack([t_open, t_high, t_low, t_close, t_vol, df['ema_fast'].values, df['ema_mid'].values, df['ema_macro'].values, t_hl, t_ret])
                        
                        norm_data_10d = np.zeros_like(raw_data_10d)
                        for d in range(raw_data_10d.shape[0]):
                            row = raw_data_10d[d]; std = np.std(row)
                            if std > 1e-9: norm_data_10d[d] = (row - np.mean(row)) / std
                        
                        danger_scores_h = self.yield_governor.analyze_historical_danger(norm_data_10d)
                        
                        # WARM-UP ACELERADO DA NUVEM DE SCHRÖDINGER
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Formando Nuvem de Schrödinger...")
                        static_V = self.cloud_tracker.generate_potential_from_volume_profile(df)
                        self.cloud_tracker.solver.update_potential(static_V)
                        for _ in range(50): self.cloud_tracker.solver.step_forward(dt=5.0, mass=0.01)
                        
                        scores_hist = []

                        for i in range(len(df)):
                            if i < window_calc:
                                self.regimes_cache.append("0|0")
                                self.signals_cache.append("0")
                                self.lbm_cache.append("0")
                                self.z_pinch_cache.append("0")
                                self.qrw_cache.append("0")
                                scores_hist.append(0)
                                continue
                            
                            slice_df = df.iloc[i-window_calc:i+1]
                            
                            r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)
                            
                            # --- COEXISTÊNCIA CALABI-YAU (SINAIS RESTAURADOS) ---
                            sig = 0
                            if r_score != 0:
                                curr_h = df.iloc[i]
                                body_h = abs(curr_h['close'] - curr_h['open'])
                                atr_val = df['atr_static'].iloc[i]
                                if not np.isnan(atr_val) and body_h > (atr_val * 1.8):
                                    sig = 1 if curr_h['close'] > curr_h['open'] else 2
                            
                            self.regimes_cache.append(f"{r_score}|{conf}")
                            self.signals_cache.append(str(sig))
                            self.lbm_cache.append("0")
                            self.z_pinch_cache.append("0")
                            self.qrw_cache.append("0")
                            
                            # SEC Calculation during Sync - Optimized to use single call with multiple internal steps
                            sec_val = "0|0|0"
                            if self.cloud_tracker:
                                # Run 20 steps internally in C++ for each candle during sync
                                self.cloud_tracker.step(slice_df, dt=1.0, steps=20)
                                    
                                m = self.cloud_tracker.get_singularity_metrics()
                                if m:
                                    is_coll = (m['singularity_strength'] > 0.10)
                                    sec_val = f"{1 if is_coll else 0}|{m['peak_price']:.2f}|{(m['schwarzschild_radius'] * self.cloud_tracker.dx):.2f}"
                            self.sec_cache.append(sec_val)
                            if len(self.sec_cache) > 300: self.sec_cache.pop(0)

                            scores_hist.append(r_score)
                            prev_s, prev_c = r_score, conf
                        
                        self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df, scores_hist)]
                        self.last_time = df.iloc[-1]['time']
                        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot v74 Concluído.")
                    
                    else:
                        # --- PROCESSO DE TICKS EM TEMPO REAL v420 (SOBERANIA QUÂNTICA) ---
                        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
                        df['ema_mid'] = df['close'].ewm(span=21, adjust=False).mean()
                        df['ema_trend'] = df['close'].ewm(span=34, adjust=False).mean()
                        df['ema_macro'] = df['close'].ewm(span=89, adjust=False).mean()
                        df['ema_gravity'] = df['close'].ewm(span=200, adjust=False).mean()
                        
                        # --- ANÁLISE DE ZONAS DE PERIGO CALABI-YAU ---
                        t_open = df['open'].values
                        t_high = df['high'].values
                        t_low = df['low'].values
                        t_close = df['close'].values
                        t_vol = df['tick_volume'].values if 'tick_volume' in df.columns else np.zeros(len(df))
                        t_hl = (df['high'] - df['low']).values
                        t_ret = df['close'].pct_change().fillna(0).values
                        
                        raw_data_10d = np.vstack([t_open, t_high, t_low, t_close, t_vol, df['ema_fast'].values, df['ema_mid'].values, df['ema_macro'].values, t_hl, t_ret])
                        
                        norm_data_10d = np.zeros_like(raw_data_10d)
                        for d in range(raw_data_10d.shape[0]):
                            row = raw_data_10d[d]; std = np.std(row)
                            if std > 1e-9: norm_data_10d[d] = (row - np.mean(row)) / std
                        
                        danger_scores = self.yield_governor.analyze_historical_danger(norm_data_10d)
                        latest_danger = danger_scores[-1]
                        cyt_danger_cache = [str(int(d)) for d in danger_scores[-len(self.regimes_cache):]]

                        # --- DETECÇÃO DE TRAPS TOPOLÓGICOS ---
                        trap_state = self.yield_governor.detect_topological_trap(norm_data_10d, t_close)

                        slice_df = df.iloc[-window_calc:]
                        r_score, conf = self.q_logic.advanced_regime_score(slice_df, prev_s, prev_c)

                        # Processa RMT Spectral Filter (Antecipado para Filtro de Soberania)
                        rmt_signal = "NOISE"
                        _, power_ratio, is_pure = self.rmt_tracker.process_spectral_filter(df)
                        if is_pure: rmt_signal = f"PURE_SIGNAL_x{power_ratio:.1f}"

                        # --- FILTRO DE SOBERANIA RMT (AUMENTA TOLERÂNCIA DO CYT) ---
                        effective_danger_threshold = 50
                        if is_pure: effective_danger_threshold = 75 # Tolerância 50% maior se o sinal for puro

                        # Determina o Status Visual Instantâneo
                        if r_score == 1:
                            status_txt = "BULL_PREVISAO" if not is_sovereign else "TSUNAMI_BULL_ATIVO"
                        elif r_score == 2:
                            status_txt = "BEAR_PREVISAO" if not is_sovereign else "TSUNAMI_BEAR_ATIVO"
                        else:
                            status_txt = "AGUARDANDO_IGNICAO"

                        # --- COEXISTÊNCIA CALABI-YAU (ALERTAS ADICIONAIS) ---
                        if latest_danger > effective_danger_threshold:
                            status_txt += " | [🚨 ALERTA TOPOLÓGICO]"
                        
                        if trap_state == "BULL_TRAP":
                            status_txt += " | [⚠️ BULL TRAP]"
                        elif trap_state == "BEAR_TRAP":
                            status_txt += " | [⚠️ BEAR TRAP]"
                        
                        is_genesis = (prev_s != r_score)
                        if is_genesis: self.genesis_count = 0
                        
                        is_sovereign = True 
                        
                        # Processa a Malha Quântica (REDUZIDO dt PARA ESTABILIDADE TEMPORAL)
                        density_schrod, needs_reset = self.cloud_tracker.step(slice_df, dt=0.2, steps=5)
                        if needs_reset:
                            self.sec_cache = ["0|0|0"] * len(self.sec_cache)

                        cloud_str = f"{self.cloud_tracker.dx:.4f}:"
                        if density_schrod is not None:
                            max_d = np.max(density_schrod)
                            cloud_arr = []
                            for i, d in enumerate(density_schrod):
                                if d > max_d * 0.10: # Aumentado threshold para 10% (Visual Clean-up)
                                    p = self.cloud_tracker.index_to_price(i)
                                    cloud_arr.append(f"{p:.2f}|{d:.4f}")
                            cloud_str += ",".join(cloud_arr)

                        # Processa LBM Dynamics
                        lbm_signal = "LAMINAR_FLOW"
                        lbm_density, lbm_velocity = self.lbm_tracker.process_tick_stream(slice_df.tail(10), steps=5)
                        if lbm_density is not None and lbm_velocity is not None:
                            lbm_signal = self.lbm_tracker.detect_squeeze_rupture(df['close'].iloc[-1], lbm_density, lbm_velocity)
                            if lbm_signal == "FLUID_RUPTURE_BULL": self.lbm_cache[-1] = "1"
                            elif lbm_signal == "FLUID_RUPTURE_BEAR": self.lbm_cache[-1] = "2"

                        # Processa MHD Plasma Z-Pinch
                        z_pinch_signal = "NEUTRAL"
                        curr_candle = df.iloc[-1]; prev_candle = df.iloc[-2]
                        if self.genesis_count % 100 == 0:
                             self.plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df, lookback=200)
                        z_idx, z_type = self.plasma_tracker.process_tick(curr_candle, prev_candle, self.plasma_zones)
                        if z_idx > 90.0:
                            z_pinch_signal = f"Z_PINCH_{z_type}"
                            if z_type == "BOTTOM_SWEEP": self.z_pinch_cache[-1] = "1"
                            elif z_type == "TOP_SWEEP": self.z_pinch_cache[-1] = "2"
                            
                        # Processa QRW
                        qrw_signal = "NEUTRAL"; qrw_lookback = 20
                        if self.qrw_tracker.is_in_range(df, lookback=qrw_lookback):
                            _, qrw_signal = self.qrw_tracker.process_qrw_skewness(df, lookback=qrw_lookback)
                            if qrw_signal == "HIDDEN_ACCUMULATION_BULL": self.qrw_cache[-1] = "1"
                            elif qrw_signal == "HIDDEN_DISTRIBUTION_BEAR": self.qrw_cache[-1] = "2"

                        # Estado em tempo real para o MT5
                        rt_regime = f"{r_score if is_sovereign else 0}|{conf}"
                        
                        # --- DEFESA CO-PILOTO QUÂNTICA ---
                        high_low = df['high'] - df['low']
                        high_close = np.abs(df['high'] - df['close'].shift(1))
                        low_close = np.abs(df['low'] - df['close'].shift(1))
                        true_range_atr = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
                        atr = true_range_atr.rolling(14).mean().iloc[-1]
                        
                        if r_score != 0:
                            self.bridge.thermodynamic_sl_tp(r_score=r_score, current_price=df['close'].iloc[-1], atr=atr, plasma_zones=self.plasma_zones, schrodinger_density=density_schrod, cloud_tracker=self.cloud_tracker)
                        
                        # --- RADAR DE ANOMALIAS ---
                        sig = 0
                        if df.iloc[-1]['time'] > self.last_time:
                            self.genesis_count += 1
                            curr = df.iloc[-1]; body = abs(curr['close'] - curr['open'])
                            if body > (atr * 1.8):
                                sig = 1 if curr['close'] > curr['open'] else 2
                                print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 👁️ NEXUS AWARE: {status_txt}")
                                
                            self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score}|{conf}")
                            self.signals_cache.pop(0); self.signals_cache.append(str(sig))
                            self.lbm_cache.pop(0); self.lbm_cache.append("0")
                            self.z_pinch_cache.pop(0); self.z_pinch_cache.append("0")
                            self.qrw_cache.pop(0); self.qrw_cache.append("0")
                            
                            # Update SEC Cache - Persistent Logic
                            if len(self.sec_cache) > 300:
                                self.sec_cache.pop(0)
                            # Append a clean slot for the new candle
                            self.sec_cache.append("0|0|0")
                            
                            scores_list = [int(r.split('|')[0]) for r in self.regimes_cache]
                            self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df.tail(len(self.regimes_cache)), scores_list)]
                            
                            prev_s, prev_c = r_score, conf
                            self.last_time = df.iloc[-1]['time']
                        
                        inst_avg = df['close'].ewm(span=89, adjust=False).mean().iloc[-1]
                        health = self.q_logic.calculate_regime_health(df)
                        status_final = f"{status_txt} | SAÚDE: {health}%"
                        
                        # Captura métricas de Singularidade SEC (Persistent Update com Arredondamento Topológico)
                        sec_str = "0|0|0"
                        if self.cloud_tracker:
                            m = self.cloud_tracker.get_singularity_metrics()
                            if m:
                                is_coll = (m['singularity_strength'] > 0.04) # Rigor unificado
                                if is_coll and not self.last_sec_state:
                                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🕳️ SINGULARIDADE ATIVA :: Strength {m['singularity_strength']:.4f}")
                                    self.last_sec_state = True
                                elif not is_coll and self.last_sec_state:
                                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ✨ SINGULARIDADE DISSIPADA :: Campo Estabilizado.")
                                    self.last_sec_state = False
                                # Round peak price to stabilize white lines (avoiding zebra effect)
                                rounded_peak = round(m['peak_price'] * 2) / 2 # Snap to 0.5 points
                                sec_str = f"{1 if is_coll else 0}|{rounded_peak:.2f}|{(m['schwarzschild_radius'] * self.cloud_tracker.dx):.2f}"
                                # If collapsed at any point in this candle, lock it in the history cache
                                if is_coll and len(self.sec_cache) > 0:
                                    self.sec_cache[-1] = sec_str

                        display_regimes = self.regimes_cache[1:] + [rt_regime]
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal};{qrw_signal};{','.join(self.lbm_cache)};{','.join(self.z_pinch_cache)};{','.join(self.qrw_cache)};{','.join(cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)}"

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
