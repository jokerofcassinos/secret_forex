"""
AETHELGARD SWARM (AGI CORE v2.0)
Orquestrador Central baseado em Actor Model (ZeroMQ).
Escuta o mercado (SUB) e consulta a Física (REQ). 
Totalmente focado em Decisão (N-Core) e Execução (R-Exec).
"""
from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
from Code.N_Core.yield_governor import YieldGovernor
from Code.N_Core.live_rht import LiveRHTTracker
from Code.N_Core.market_qcd import MarketQCDTracker
import time
import numpy as np
import pandas as pd
import zmq
import pickle
import threading
import socket
import logging
import sys

from Code.N_Core.swarm_bus import create_subscriber, create_request_client, create_publisher, PORT_TICK_FEED, PORT_Q_MATH, PORT_CONTROL, TOPIC_MARKET_BAR, TOPIC_CONTROL
from Code.R_Exec.mt5_bridge import MT5NeuralBridge

# Windows UTF-8 console fix
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

nexus_data_str = "0;0;INIT;0;0;0;0;0"
current_mt5_tf = None

def run_tcp_server():
    """Servidor TCP puro e ultra-leve para substituir o Flask. Responde instantaneamente ao MT5."""
    global nexus_data_str, current_mt5_tf
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('127.0.0.1', 5000))
        server_socket.listen(5)
    except Exception as e:
        print(f"❌ SWARM CORE :: Erro ao iniciar Servidor TCP: {e}")
        return

    while True:
        try:
            client_socket, _ = server_socket.accept()
            request = client_socket.recv(1024) 
            
            # Parseia o parametro tf da URL: GET /nexus?tf=16385 HTTP/1.1
            try:
                req_str = request.decode('utf-8')
                if "GET /nexus?tf=" in req_str:
                    tf_str = req_str.split("GET /nexus?tf=")[1].split(" ")[0]
                    current_mt5_tf = int(tf_str)
            except Exception:
                pass
            
            # Monta a resposta HTTP
            response_body = nexus_data_str.encode('utf-8')
            http_response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Connection: close\r\n"
                b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
                b"\r\n" + response_body
            )
            
            client_socket.sendall(http_response)
            client_socket.close()
        except Exception as e:
            pass 

class AethelgardSwarm:
    def __init__(self, symbol="GER40.cash"):
        self.symbol = symbol
        self.bridge = MT5NeuralBridge(symbol)
        self.q_logic = QuantumIndicators()
        self.rht_tracker = LiveRHTTracker(symbol, lookback=300)
        self.alchemist = MSNRAlchemist()
        self.oracle = QuantumOracle(simulations=5000)
        self.yield_governor = YieldGovernor(danger_window=30, danger_threshold=25.0)
        
        self.is_running = False
        self.active_tf = None
        
        # Caches neurais
        self.regimes_cache = []
        self.signals_cache = []
        self.lbm_cache = []
        self.z_pinch_cache = []
        self.qrw_cache = []
        self.dots_cache = []
        self.sec_cache = []
        self.rht_cache = []
        self.qcd_cache = []
        self.cyt_danger_cache = []
        self.last_time = 0
        self.genesis_count = 0
        self.prev_s = 0
        self.prev_c = 0
        self.is_sovereign = False
        
        # Redes ZeroMQ
        self.sub_context, self.sub_socket = create_subscriber(PORT_TICK_FEED, TOPIC_MARKET_BAR)
        self.req_context, self.req_socket = create_request_client(PORT_Q_MATH)
        self.ctrl_context, self.ctrl_socket = create_publisher(PORT_CONTROL)

    def startup(self):
        print(f"--- INICIANDO MOTOR SWARM v2.0 [AGI CORE] :: {self.symbol} ---")
        if not self.bridge.initialize(): return False
        threading.Thread(target=run_tcp_server, daemon=True).start()
        self.is_running = True
        return True

    def fetch_quantum_state(self):
        """Dispara um REQ para o nó Q-MATH e aguarda a resposta do estado atual"""
        try:
            self.req_socket.send(b"GET_STATE")
            if self.req_socket.poll(2000) & zmq.POLLIN:
                reply = self.req_socket.recv()
                return pickle.loads(reply)
            else:
                print("⚠️ SWARM CORE :: Timeout na conexão com Q-Math Node.")
                self.req_socket.close()
                self.req_context.term()
                self.req_context, self.req_socket = create_request_client(PORT_Q_MATH)
                return None
        except Exception as e:
            print(f"❌ SWARM CORE :: Erro na requisição quântica: {e}")
            return None

    def initialize_caches(self, df):
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Sincronizando Malha Neural N-Core...")
        window_calc = 200
        
        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_mid'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema_trend'] = df['close'].ewm(span=34, adjust=False).mean()
        df['ema_macro'] = df['close'].ewm(span=89, adjust=False).mean()
        df['ema_gravity'] = df['close'].ewm(span=200, adjust=False).mean()
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr_full = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr_static'] = tr_full.rolling(14).mean()

        qcd_hist_tracker = MarketQCDTracker(lookback_window=20)
        
        # Retrospectiva Histórica de Alta Frequência (Física)
        try:
            import sys
            import os
            cpp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Code/CPP_Engine'))
            if cpp_path not in sys.path:
                sys.path.append(cpp_path)
                
            if os.name == 'nt' and os.path.exists(r"D:\msys64\mingw64\bin"):
                os.add_dll_directory(r"D:\msys64\mingw64\bin")
            
            import cyt_engine
            import lbm_engine
            import qgc_engine
            cyt_hist = cyt_engine.CYTEngine()
            lbm_hist = lbm_engine.LBMEngine(200, 1.2)
            qgc_hist = qgc_engine.QGCEngine()
            has_cpp_hist = True
        except Exception as e:
            print(f"⚠️ N-Core :: Falha ao carregar motores historicos ({e})")
            has_cpp_hist = False
        
        scores_hist = []
        qgc_str = ""
        
        for i in range(len(df)):
            if i < window_calc:
                self.regimes_cache.append("0|0")
                self.signals_cache.append("0")
                self.lbm_cache.append("0")
                self.z_pinch_cache.append("0")
                self.qrw_cache.append("0")
                self.qcd_cache.append("0")
                self.cyt_danger_cache.append("0")
                scores_hist.append(0)
                continue
            
            slice_df = df.iloc[i-window_calc:i+1]
            curr_h = df.iloc[i]
            r_score, conf = self.q_logic.advanced_regime_score(slice_df, self.prev_s, self.prev_c)
            
            sig = 0
            if r_score != 0:
                body_h = abs(curr_h['close'] - curr_h['open'])
                atr_val = df['atr_static'].iloc[i]
                if not np.isnan(atr_val) and body_h > (atr_val * 1.8):
                    sig = 1 if curr_h['close'] > curr_h['open'] else 2
            
            self.regimes_cache.append(f"{r_score}|{conf}")
            self.signals_cache.append(str(sig))
            
            # --- Injeção de Inteligência Histórica ---
            lbm_sig_hist = "0"
            cyt_danger_hist = "0"
            
            if has_cpp_hist:
                try:
                    # Motor AdS/CFT
                    if (i % 2 == 0):
                        data_10d = np.zeros((10, len(slice_df)))
                        data_10d[0, :] = slice_df['open'].values
                        data_10d[1, :] = slice_df['high'].values
                        data_10d[2, :] = slice_df['low'].values
                        data_10d[3, :] = slice_df['close'].values
                        data_10d[4, :] = slice_df['tick_volume'].values
                        data_10d[5, :] = slice_df['close'].pct_change().bfill().values
                        data_10d[6, :] = (slice_df['high'] - slice_df['low']).values
                        data_10d[7, :] = slice_df['close'].rolling(5).mean().bfill().values
                        data_10d[8, :] = slice_df['tick_volume'].rolling(5).mean().bfill().values
                        data_10d[9, :] = (slice_df['close'] - slice_df['open']).values
                        
                        flow = cyt_hist.analyze_manifold_flow(data_10d)
                        defs = flow["deformation"]
                        if len(defs) > 50:
                            m_def, s_def = np.mean(defs), np.std(defs)
                            if s_def > 1e-9:
                                z_def = (defs[-1] - m_def) / s_def
                                if z_def > 5.5:
                                    cyt_danger_hist = str(min(100, int(50 + (z_def * 8))))
                        
                    # Motor LBM (Hidrodinâmica)
                    vols = slice_df['tick_volume'].values
                    m_vol = np.mean(vols)
                    if m_vol > 0:
                        v_ratio = vols[-1] / m_vol
                        lbm_hist.inject_liquidity(100, min(2.0, v_ratio), 0.0) 
                        lbm_hist.step()
                        
                        atr_val = df['atr_static'].iloc[i]
                        body = abs(curr_h['close'] - curr_h['open'])
                        if v_ratio > 3.0:
                            if body < (atr_val * 0.2): 
                                lbm_sig_hist = "1" if curr_h['close'] < curr_h['open'] else "2"
                            elif body > (atr_val * 2.5): 
                                lbm_sig_hist = "1" if curr_h['close'] > curr_h['open'] else "2"
                except:
                    pass
            
            self.lbm_cache.append(lbm_sig_hist)
            self.z_pinch_cache.append("0")
            self.qrw_cache.append("0")
            
            qcd_sig = qcd_hist_tracker.detect_fission(slice_df)
            if "FISSION_EXPANSION_UP" in qcd_sig: self.qcd_cache.append("1")
            elif "FISSION_EXPANSION_DOWN" in qcd_sig: self.qcd_cache.append("2")
            elif "FISSION" in qcd_sig: self.qcd_cache.append("1" if curr_h['close'] > curr_h['open'] else "2")
            else: self.qcd_cache.append("0")
                
            self.cyt_danger_cache.append(cyt_danger_hist)
            self.sec_cache.append("0|0|0")
            if len(self.sec_cache) > 300: self.sec_cache.pop(0)

            scores_hist.append(r_score)
            self.prev_s, self.prev_c = r_score, conf
            
            # --- QGC Engine (Hawking Decay) apenas no final do boot ---
            if i == len(df) - 1 and has_cpp_hist:
                try:
                    hist_window = 1000
                    if len(df) >= hist_window:
                        qgc_slice = df.tail(hist_window)
                        v_mean = qgc_slice['tick_volume'].mean()
                        # Threshold de Genesis do Vidro Quantico: Volume > 5.5x a media
                        m_threshold = v_mean * 5.5 
                        
                        res = qgc_hist.compute_hawking_decay(
                            qgc_slice['close'].values, 
                            qgc_slice['tick_volume'].values, 
                            qgc_slice['atr_static'].fillna(0).values, 
                            m_threshold
                        )
                        r_masses = res.get("residual_masses", [])
                        c_masses = res.get("centers_of_mass", [])
                        ages = res.get("ages", [])
                        
                        # Monta a string QGC (Idade|Preco|MassaNormalizada_0_a_10)
                        qgc_parts = []
                        for m, p, a in zip(r_masses, c_masses, ages):
                            if m > 0:
                                norm_mass = min(10.0, (m / m_threshold) * 2.0)
                                if norm_mass > 0.5: # Só envia o que ainda tem alguma relevância visual
                                    qgc_parts.append(f"{int(a)}|{p:.2f}|{norm_mass:.1f}")
                        qgc_str = ",".join(qgc_parts)
                except Exception as e:
                    print(f"⚠️ Erro no QGC Boot: {e}")
        
        self.qgc_data_str = qgc_str
        self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df, scores_hist)]
        self.last_time = df.iloc[-1]['time']
        self.rht_cache = ["0"] * 300
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot N-Core Concluído. Memória Quântica Preenchida.")

    def live_evolution_loop(self):
        global nexus_data_str, current_mt5_tf
        print("🧠 SWARM CORE :: Loop Evolutivo Iniciado. Aguardando Nexus Router...")
        
        try:
            while self.is_running:
                if current_mt5_tf is not None and self.active_tf != current_mt5_tf:
                    self.active_tf = current_mt5_tf
                    print(f"\n🌀 SWARM CORE :: Detectada Mudança Dimensional (TF: {self.active_tf}). Realinhando Redes...")
                    self.regimes_cache.clear()
                    self.sec_cache.clear()
                    self.dots_cache.clear()
                    self.qcd_cache.clear()
                    self.cyt_danger_cache.clear()
                    self.last_time = 0
                    ctrl_payload = pickle.dumps({"action": "CHANGE_TF", "timeframe": self.active_tf})
                    self.ctrl_socket.send_multipart([TOPIC_CONTROL.encode('utf-8'), ctrl_payload])
                    time.sleep(0.5)

                latest_df = None
                while True:
                    try:
                        msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                        topic = msg[0].decode('utf-8')
                        if topic == TOPIC_MARKET_BAR:
                            payload = pickle.loads(msg[1])
                            latest_df = payload.get("data")
                    except zmq.Again:
                        break
                    except Exception as e:
                        print(f"\n❌ SWARM CORE :: Erro de Leitura SUB: {e}")
                        break
                        
                if latest_df is not None:
                    df = latest_df
                    current_close = df['close'].iloc[-1]
                    if not self.regimes_cache:
                        self.initialize_caches(df)
                    q_state = self.fetch_quantum_state()
                    
                    if q_state and q_state.get("status") == "ACTIVE":
                        df['ema_macro'] = df['close'].ewm(span=89, adjust=False).mean()
                        window_calc = 200
                        slice_df = df.iloc[-window_calc:]
                        r_score, conf = self.q_logic.advanced_regime_score(slice_df, self.prev_s, self.prev_c)

                        if r_score == 1: status_txt = "BULL_PREVISAO" if not self.is_sovereign else "TSUNAMI_BULL_ATIVO"
                        elif r_score == 2: status_txt = "BEAR_PREVISAO" if not self.is_sovereign else "TSUNAMI_BEAR_ATIVO"
                        else: status_txt = "AGUARDANDO_IGNICAO"

                        is_genesis = (self.prev_s != r_score)
                        if is_genesis: self.genesis_count = 0
                        self.is_sovereign = True 
                        inst_avg = df['ema_macro'].iloc[-1]
                        health = self.q_logic.calculate_regime_health(df)
                        status_final = f"{status_txt} | SAÚDE: {health}%"
                        
                        if df.iloc[-1]['time'] > self.last_time:
                            self.genesis_count += 1
                            self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score}|{conf}")
                            self.signals_cache.pop(0); self.signals_cache.append("0")
                            self.lbm_cache.pop(0); self.lbm_cache.append("0")
                            self.z_pinch_cache.pop(0); self.z_pinch_cache.append("0")
                            self.qrw_cache.pop(0); self.qrw_cache.append("0")
                            self.qcd_cache.pop(0); self.qcd_cache.append("0")
                            self.cyt_danger_cache.pop(0); self.cyt_danger_cache.append("0")
                            self.sec_cache.append("0|0|0")
                            if len(self.sec_cache) > 300: self.sec_cache.pop(0)
                            scores_list = [int(r.split('|')[0]) for r in self.regimes_cache]
                            self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df.tail(len(self.regimes_cache)), scores_list)]
                            self.prev_s, self.prev_c = r_score, conf
                            self.last_time = df.iloc[-1]['time']
                            
                            # Atualiza Hawking Decay para o novo candle
                            try:
                                import sys
                                if 'qgc_hist' in locals() or 'qgc_hist' in globals() or hasattr(self, 'qgc_data_str'):
                                    import qgc_engine
                                    hist_window = 1000
                                    if len(df) >= hist_window:
                                        qgc_slice = df.tail(hist_window)
                                        v_mean = qgc_slice['tick_volume'].mean()
                                        m_threshold = v_mean * 3.5 # Reduzido de 5.5 para capturar mais Condensados
                                        
                                        qgc_engine_live = qgc_engine.QGCEngine()
                                        res = qgc_engine_live.compute_hawking_decay(
                                            qgc_slice['close'].values, 
                                            qgc_slice['tick_volume'].values, 
                                            qgc_slice['atr_static'].fillna(0).values, 
                                            m_threshold
                                        )
                                        r_masses = res.get("residual_masses", [])
                                        c_masses = res.get("centers_of_mass", [])
                                        ages = res.get("ages", [])
                                        
                                        qgc_parts = []
                                        for m, p, a in zip(r_masses, c_masses, ages):
                                            if m > 0:
                                                norm_mass = min(10.0, (m / m_threshold) * 2.0)
                                                if norm_mass > 0.5:
                                                    qgc_parts.append(f"{int(a)}|{p:.2f}|{norm_mass:.1f}")
                                        self.qgc_data_str = ",".join(qgc_parts)
                            except Exception as e:
                                pass

                        rt_regime = f"{r_score if self.is_sovereign else 0}|{conf}"
                        display_regimes = self.regimes_cache[1:] + [rt_regime]
                        cloud_str = q_state.get("cloud_str", "0.0001:")
                        lbm_signal = q_state.get("lbm_signal", "LAMINAR_FLOW")
                        z_pinch_signal = q_state.get("z_pinch_signal", "NEUTRAL")
                        rmt_signal = q_state.get("rmt_signal", "NEUTRAL")
                        qrw_signal = q_state.get("qrw_signal", "NEUTRAL")
                        sec_m = q_state.get("sec_metrics")
                        
                        if lbm_signal == "FLUID_RUPTURE_BULL": self.lbm_cache[-1] = "1"
                        elif lbm_signal == "FLUID_RUPTURE_BEAR": self.lbm_cache[-1] = "2"
                        if "BOTTOM_SWEEP" in z_pinch_signal: self.z_pinch_cache[-1] = "1"
                        elif "TOP_SWEEP" in z_pinch_signal: self.z_pinch_cache[-1] = "2"
                        if qrw_signal == "HIDDEN_ACCUMULATION_BULL": self.qrw_cache[-1] = "1"
                        elif qrw_signal == "HIDDEN_DISTRIBUTION_BEAR": self.qrw_cache[-1] = "2"
                        
                        qcd_signal = q_state.get("qcd_signal", "CONFINED")
                        cyt_danger = q_state.get("cyt_danger", 0.0)
                        if "FISSION_EXPANSION_UP" in qcd_signal: self.qcd_cache[-1] = "1"
                        elif "FISSION_EXPANSION_DOWN" in qcd_signal: self.qcd_cache[-1] = "2"
                        elif "FISSION" in qcd_signal and self.qcd_cache[-1] == "0":
                            self.qcd_cache[-1] = "1" if current_close > df['open'].iloc[-1] else "2"
                        
                        self.cyt_danger_cache[-1] = str(int(cyt_danger))
                        high_low = df['high'] - df['low']
                        high_close = np.abs(df['high'] - df['close'].shift(1))
                        low_close = np.abs(df['low'] - df['close'].shift(1))
                        true_range_atr = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
                        atr = true_range_atr.rolling(14).mean().iloc[-1]
                        
                        self.bridge.thermodynamic_sl_tp(
                            r_score=r_score, 
                            current_price=current_close, 
                            atr=atr, 
                            plasma_zones=q_state.get("plasma_zones"), 
                            schrodinger_density=q_state.get("density_schrod"),
                            cloud_tracker=None
                        )

                        sec_str = "0|0|0"
                        if sec_m:
                            is_coll = (sec_m.get('singularity_strength', 0) > 0.04)
                            rounded_peak = round(sec_m.get('peak_price', current_close) * 2) / 2
                            sec_str = f"{1 if is_coll else 0}|{rounded_peak:.2f}|{(sec_m.get('schwarzschild_radius', 0)):.2f}"
                            if is_coll and len(self.sec_cache) > 0: self.sec_cache[-1] = sec_str
                        else:
                            sec_str = f"0|{current_close:.2f}|0.00"

                        rht_status_local = "PURIFYING"
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal};{qrw_signal};{','.join(self.lbm_cache)};{','.join(self.z_pinch_cache)};{','.join(self.qrw_cache)};{','.join(self.cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_status_local};{','.join(self.rht_cache)};{qcd_signal};{','.join(self.qcd_cache)};{self.qgc_data_str}"
                else:
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.sub_socket.close()
        self.req_socket.close()
        self.sub_context.term()
        self.req_context.term()
        print("\n🧠 SWARM CORE :: Desligado.")

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aethelgard Swarm AGI Core")
    parser.add_argument('--symbol', type=str, default="GER40.cash", help='Symbol to trade')
    args = parser.parse_args()
    agi = AethelgardSwarm(symbol=args.symbol)
    if agi.startup():
        agi.live_evolution_loop()
