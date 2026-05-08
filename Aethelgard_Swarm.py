"""
AETHELGARD SWARM (AGI CORE v2.1 - STABLE)

Orquestrador Central baseado em Actor Model (ZeroMQ).
Escuta o mercado (SUB) e consulta a Física (REQ). 
Totalmente focado em Decisão (N-Core) e Execução (R-Exec).
"""
import time
import numpy as np
import pandas as pd
import zmq
import pickle
import threading
import socket
import sys
import os
import argparse

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++
if os.name == 'nt':
    # 1. Mingw64 Binaries
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    
    # 2. NEXUS CPP Engines (Root & Bin)
    root_path = os.path.dirname(os.path.abspath(__file__))
    bin_path = os.path.join(root_path, "Code", "CPP_Engine", "bin")
    
    for p in [root_path, bin_path]:
        if os.path.exists(p):
            try:
                os.add_dll_directory(p)
            except Exception: pass
            if p not in sys.path:
                sys.path.insert(0, p)

from Code.N_Core.quantum_indicators import QuantumIndicators
from Code.N_Core.msnr_alchemist import MSNRAlchemist
from Code.N_Core.quantum_oracle import QuantumOracle
from Code.N_Core.yield_governor import YieldGovernor
from Code.N_Core.live_rht import LiveRHTTracker
from Code.N_Core.market_qcd import MarketQCDTracker



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
    """Servidor TCP puro e ultra-leve para responder instantaneamente ao MT5."""
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
            try:
                req_str = request.decode('utf-8')
                if "GET /nexus?tf=" in req_str:
                    tf_str = req_str.split("GET /nexus?tf=")[1].split(" ")[0]
                    current_mt5_tf = int(tf_str)
            except Exception:
                pass
            
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
        except Exception:
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
        self.qgc_data_str = ""
        
        self.sub_context, self.sub_socket = create_subscriber(PORT_TICK_FEED, TOPIC_MARKET_BAR)
        self.req_context, self.req_socket = create_request_client(PORT_Q_MATH)
        self.ctrl_context, self.ctrl_socket = create_publisher(PORT_CONTROL)

    def startup(self):
        print(f"--- INICIANDO MOTOR SWARM v3.3 [AGI CORE] :: {self.symbol} ---")
        if not self.bridge.initialize(): return False
        threading.Thread(target=run_tcp_server, daemon=True).start()
        self.is_running = True
        return True

    def fetch_quantum_state(self, current_regime=0):
        try:
            self.req_socket.send(f"GET_STATE|{current_regime}".encode('utf-8'))
            if self.req_socket.poll(2000) & zmq.POLLIN:
                reply = self.req_socket.recv()
                return pickle.loads(reply)
            else:
                self.req_socket.close()
                self.req_context.term()
                self.req_context, self.req_socket = create_request_client(PORT_Q_MATH)
                return None
        except Exception:
            return None

    def initialize_caches(self, df):
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Sincronizando Malha Neural N-Core...")
        window_calc = 200
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        tr_full = np.maximum(high_low, np.maximum(high_close, low_close))
        df['atr_static'] = tr_full.rolling(14).mean()
        
        try:
            import cyt_engine, qgc_engine
            cyt_hist = cyt_engine.CYTEngine()
            qgc_hist = qgc_engine.QGCEngine()
            has_cpp_hist = True
        except Exception:
            has_cpp_hist = False

        from Code.N_Core.fluid_dynamics import LBMFluidDynamics
        p_min_global, p_max_global = df['low'].min() - 100, df['high'].max() + 100
        lbm_boot = LBMFluidDynamics(p_min_global, p_max_global, bins=100)
        
        from Code.N_Core.market_qcd import MarketQCDTracker
        qcd_hist_tracker = MarketQCDTracker()
        
        self.regimes_cache = []
        self.signals_cache = []
        self.lbm_cache = []
        self.z_pinch_cache = []
        self.qrw_cache = []
        self.qcd_cache = []
        self.cyt_danger_cache = []
        self.sec_cache = []
        
        scores_hist = []
        self.prev_s, self.prev_c = 0, 0
        
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
            
            slice_df = df.iloc[:i+1]
            curr_h = df.iloc[i]
            r_score, conf = self.q_logic.advanced_regime_score(slice_df.tail(200), self.prev_s, self.prev_c)
            self.prev_s, self.prev_c = r_score, conf

            
            self.regimes_cache.append(f"{r_score}|{conf}")
            self.signals_cache.append("0")
            
            lbm_sig_hist, cyt_danger_hist = "0", "0"
            if has_cpp_hist:
                try:
                    data_10d = np.zeros((10, 50))
                    d_slice = slice_df.tail(50)
                    data_10d[0,:] = d_slice['open'].values; data_10d[1,:] = d_slice['high'].values
                    data_10d[2,:] = d_slice['low'].values; data_10d[3,:] = d_slice['close'].values
                    data_10d[4,:] = d_slice['tick_volume'].values
                    flow = cyt_hist.analyze_manifold_flow(data_10d)
                    def_arr = flow.get("deformation", np.zeros(1))
                    ricci_h = float(def_arr[-1]) if len(def_arr) > 0 else 0.0
                    if ricci_h >= 1.5: cyt_danger_hist = str(int(ricci_h * 100))
                    
                    l_den, l_vel = lbm_boot.process_tick_stream(slice_df.tail(5), steps=2)
                    if l_den is not None:
                        res_lbm = lbm_boot.detect_squeeze_rupture(slice_df.tail(150), l_den, l_vel, current_regime=r_score)
                        if res_lbm == "BOSONIC_SQUEEZE": lbm_sig_hist = "3"
                        elif res_lbm == "FLUID_RUPTURE_BULL": lbm_sig_hist = "1"
                        elif res_lbm == "FLUID_RUPTURE_BEAR": lbm_sig_hist = "2"
                except: pass
            
            self.lbm_cache.append(lbm_sig_hist)
            self.cyt_danger_cache.append(cyt_danger_hist)
            self.z_pinch_cache.append("0"); self.qrw_cache.append("0")
            
            qcd_sig = qcd_hist_tracker.detect_fission(slice_df)
            if "FISSION_EXPANSION_UP" in qcd_sig: self.qcd_cache.append("1")
            elif "FISSION_EXPANSION_DOWN" in qcd_sig: self.qcd_cache.append("2")
            elif "FISSION" in qcd_sig: self.qcd_cache.append("1" if curr_h['close'] > curr_h['open'] else "2")
            else: self.qcd_cache.append("0")
            
            self.sec_cache.append("0|0|0")
            if len(self.sec_cache) > 300: self.sec_cache.pop(0)
            scores_hist.append(r_score)
            
            if i == len(df) - 1 and has_cpp_hist:
                try:
                    q_slc = df.tail(500)
                    m_thr = q_slc['tick_volume'].mean() * 2.0
                    res = qgc_hist.compute_hawking_decay(q_slc['close'].values, q_slc['tick_volume'].values, q_slc['atr_static'].fillna(0).values, m_thr)
                    q_parts = [f"{int(a)}|{p:.2f}|{min(10.0, (m/m_thr)*2):.1f}" for m, p, a in zip(res.get("residual_masses", []), res.get("centers_of_mass", []), res.get("ages", [])) if m > 0]
                    self.qgc_data_str = ",".join(q_parts)
                except: pass
        
        # Ocultação Tática: Silenciando setas e traços para foco no Regime/LBM
        self.dots_cache = ["0"] * len(df)
        self.qcd_cache = ["0"] * len(df)

        self.last_time = df.iloc[-1]['time']
        self.rht_cache = ["0"] * 300
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot N-Core Concluído. Memória Purificada.")

    def live_evolution_loop(self):
        global nexus_data_str, current_mt5_tf
        print("🧠 SWARM CORE :: Loop Evolutivo Iniciado.")
        try:
            while self.is_running:
                if current_mt5_tf is not None and self.active_tf != current_mt5_tf:
                    self.active_tf = current_mt5_tf
                    self.regimes_cache.clear(); self.sec_cache.clear(); self.dots_cache.clear()
                    self.qcd_cache.clear(); self.cyt_danger_cache.clear(); self.last_time = 0
                    ctrl_payload = pickle.dumps({"action": "CHANGE_TF", "timeframe": self.active_tf})
                    self.ctrl_socket.send_multipart([TOPIC_CONTROL.encode('utf-8'), ctrl_payload])
                    time.sleep(0.5)

                latest_df = None
                while True:
                    try:
                        msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                        if msg[0].decode('utf-8') == TOPIC_MARKET_BAR:
                            latest_df = pickle.loads(msg[1]).get("data")
                    except zmq.Again: break
                    except: break
                        
                if latest_df is not None:
                    df = latest_df
                    if not self.regimes_cache: self.initialize_caches(df)
                    
                    window_calc = 200
                    r_score, conf = self.q_logic.advanced_regime_score(df.tail(window_calc), self.prev_s, self.prev_c)
                    q_state = self.fetch_quantum_state(current_regime=r_score)
                    
                    if q_state and q_state.get("status") == "ACTIVE":
                        inst_avg = df['close'].ewm(span=89, adjust=False).mean().iloc[-1]
                        health = self.q_logic.calculate_regime_health(df)
                        status_txt = "TSUNAMI_BULL" if r_score == 1 else ("TSUNAMI_BEAR" if r_score == 2 else "SCANNING")
                        status_final = f"{status_txt} | CONF: {health}%"
                    else:
                        inst_avg = df['close'].mean()
                        health = 0
                        status_final = "PHYSICS_OFFLINE | RECONNECTING..."
                        q_state = {}

                    if df.iloc[-1]['time'] > self.last_time:
                        self.regimes_cache.pop(0); self.regimes_cache.append(f"{r_score}|{conf}")
                        self.signals_cache.pop(0); self.signals_cache.append("0")
                        self.lbm_cache.pop(0); self.lbm_cache.append("0")
                        self.cyt_danger_cache.pop(0); self.cyt_danger_cache.append("0")
                        self.qcd_cache.pop(0); self.qcd_cache.append("0")
                        self.sec_cache.append("0|0|0")
                        if len(self.sec_cache) > 300: self.sec_cache.pop(0)
                        s_list = [int(r.split('|')[0]) for r in self.regimes_cache]
                        self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df.tail(len(self.regimes_cache)), s_list)]
                        self.prev_s, self.prev_c = r_score, conf
                        self.last_time = df.iloc[-1]['time']

                    lbm_s = q_state.get("lbm_signal", "LAMINAR_FLOW")
                    if lbm_s == "FLUID_RUPTURE_BULL": self.lbm_cache[-1] = "1"
                    elif lbm_s == "FLUID_RUPTURE_BEAR": self.lbm_cache[-1] = "2"
                    elif lbm_s == "BOSONIC_SQUEEZE": self.lbm_cache[-1] = "3"
                    
                    qcd_s = q_state.get("qcd_signal", "CONFINED")
                    if "FISSION_EXPANSION_UP" in qcd_s: self.qcd_cache[-1] = "1"
                    elif "FISSION_EXPANSION_DOWN" in qcd_s: self.qcd_cache[-1] = "2"
                    
                    ricci_c = q_state.get("ricci_curvature", 0.0)
                    h_ent = q_state.get("h_entropy", 0.0)
                    coll_s = "1" if q_state.get("is_collapsed", False) else "0"
                    qrw_h = q_state.get("qrw_history", "")
                    
                    self.cyt_danger_cache[-1] = str(int(ricci_c * 100))
                    
                    sec_m = q_state.get("sec_metrics")
                    sec_str = "0|0|0"
                    if sec_m and sec_m.get('singularity_strength', 0) > 0.04:
                        sec_str = f"1|{sec_m.get('peak_price'):.2f}|{sec_m.get('schwarzschild_radius'):.2f}"
                        self.sec_cache[-1] = sec_str

                    # 7. MÉTRICAS DE WYCKOFF-QUANTUM (DISABLED)
                    # w_metrics = self.q_logic.get_market_state(df, q_state.get("lbm_density", np.zeros(100)), q_state.get("lbm_velocity", np.zeros(100)), r_score)
                    # w_str = f"{w_metrics['score']}|{w_metrics['wyckoff_phase']}|{w_metrics['divergence']}|{w_metrics['strength']}"
                    w_str = "0|0|0|0"

                    rht_s = q_state.get("rht_status", "PURIFYING")
                    rht_h = q_state.get("rht_history", "")

                    nexus_data_str = f"0;0;{status_final};0;{','.join(self.regimes_cache)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{q_state.get('cloud_str')};{lbm_s};{q_state.get('z_pinch_signal')};{q_state.get('rmt_signal')};{q_state.get('qrw_signal')};{','.join(self.lbm_cache)};{ricci_c:.4f};{h_ent:.4f};{','.join(self.cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_s};{coll_s};{qcd_s};{','.join(self.qcd_cache)};{self.qgc_data_str};{w_str};{qrw_h};{rht_h}"
                else: time.sleep(0.01)
        except KeyboardInterrupt: self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.sub_socket.close(); self.req_socket.close()
        self.sub_context.term(); self.req_context.term()
        print("\n🧠 SWARM CORE :: Desligado.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Aethelgard Swarm - AGI Core")
    parser.add_argument('--asset', type=str, default="BTCUSD", help='Ativo para operação')
    args = parser.parse_args()
    
    agi = AethelgardSwarm(symbol=args.asset)
    if agi.startup(): agi.live_evolution_loop()
