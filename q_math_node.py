"""
Q-MATH NODE (ZMQ SUB / REP Node - v70.0)
Função: Quantum Fluid Splatting Engine (v70.0).
Nuvem RELATIVA que orbita o zero matemático para paridade 1:1 absoluta.
"""
import time
import threading
import MetaTrader5 as mt5
import pickle
import sys
import os
import zmq
import concurrent.futures
import numpy as np
import pandas as pd

if os.name == 'nt':
    root_path = os.path.dirname(__file__)
    if os.path.exists(root_path):
        os.add_dll_directory(root_path)
    if root_path not in sys.path: sys.path.insert(0, root_path)
    if os.path.exists(r"D:\msys64\mingw64\bin"): os.add_dll_directory(r"D:\msys64\mingw64\bin")

from Code.N_Core.swarm_bus import create_subscriber, create_reply_server, PORT_TICK_FEED, PORT_Q_MATH, TOPIC_MARKET_BAR
from Code.N_Core.quantum_clouds import QuantumCloudTracker
from Code.N_Core.fluid_dynamics import LBMFluidDynamics
from Code.N_Core.plasma_market import PlasmaMarketTracker
from Code.N_Core.random_matrix import RandomMatrixTracker
from Code.N_Core.quantum_walk import QRWTracker
from Code.N_Core.market_qcd import MarketQCDTracker
from Code.N_Core.live_rht import LiveRHTTracker
from Code.N_Core.quantum_projection import QuantumPreCognitionNode
import cyt_engine

class QMathNode:
    def __init__(self):
        print("⚛️ Q-MATH :: Sincronizando subsistemas [QUANTUM FLUID v70.0]...")
        self.sub_context, self.sub_socket = create_subscriber(PORT_TICK_FEED, TOPIC_MARKET_BAR)
        self.rep_context, self.rep_socket = create_reply_server(PORT_Q_MATH)
        self.is_running = False
        self.cloud_tracker = None
        self.lbm_tracker = None
        self.plasma_tracker = None
        self.rmt_tracker = None
        self.qrw_tracker = None
        self.qcd_tracker = None
        self.rht_tracker = None
        self.cyt = cyt_engine.CYTEngine()
        self.precog_node = None
        
        self.current_symbol = "GER40.cash"
        self.active_tf = None
        self.last_processed_symbol = None
        self.current_regime_context = 0
        self.current_pti_context = 0.0

        self.current_state = {
            "status": "INITIALIZING",
            "cloud_str": "0.0:0.0:0.0:",
            "lbm_signal": "LAMINAR_FLOW"
        }
        
        self.last_raw_density = None
        self.last_sync_price = None
        self.state_lock = threading.Lock()
        print(f"✅ Q-MATH :: Subsistemas Prontos. Aguardando Fluxo em {PORT_TICK_FEED}...")

    def process_market_data(self, payload):
        try:
            df = payload.get("data")
            if df is None or df.empty: return
            
            tf = payload.get("timeframe")
            payload_sym = payload.get("symbol", self.current_symbol)

            if (tf is not None and self.active_tf != tf) or (self.last_processed_symbol != payload_sym):
                print(f"\n⚛️ Q-MATH :: Reset Dimensional para {payload_sym} ({tf})")
                self.active_tf = tf; self.last_processed_symbol = payload_sym; self.current_symbol = payload_sym
                self.cloud_tracker = None; self.lbm_tracker = None; self.plasma_tracker = None
                self.rmt_tracker = None; self.qrw_tracker = None; self.rht_tracker = None; self.qcd_tracker = None; self.precog_node = None

            current_close = df['close'].iloc[-1]
            # [v71.1] Global Re-anchoring: Absolute Reference Manifold recalculated every tick
            half_range = 1200.0 
            p_min = current_close - half_range
            p_max = current_close + half_range

            if self.cloud_tracker is None:
                # [V68.0] Singularity Glow Engine - Absolute Reference Manifold
                self.cloud_tracker = QuantumCloudTracker(price_min=p_min, price_max=p_max, bins=512)
                self.cloud_tracker.initialize_wave(current_close, sigma=(self.cloud_tracker.dx * 110.0))
                self.last_sync_price = current_close
                self.cloud_trail = []
                self.last_physics_time = None
                print(f"⚛️ Q-MATH :: Quantum Fluid Engine v71.1 Iniciado em {payload_sym}.")
                
                # [SINGULARITY WARM-UP] v71.1 Volumetric Plasma (31pt Blur)
                warmup_size = min(100, len(df) - 11)
                if warmup_size > 0:
                    print(f"🚀 Q-MATH :: Materializando Plasma Volumétrico ({warmup_size} snapshots)...")
                    kernel = np.ones(31) / 31.0
                    for i in range(len(df) - warmup_size, len(df)):
                        sub_df = df.iloc[:i+1].copy()
                        c_close = sub_df['close'].iloc[-1]
                        
                        # Dynamic Re-anchoring during warmup
                        w_p_min = c_close - half_range
                        w_p_max = c_close + half_range
                        self.cloud_tracker.price_min = w_p_min
                        self.cloud_tracker.price_max = w_p_max
                        
                        dt_phys = 2.0
                        
                        # Absolute Space Physics (v71.1)
                        density, _ = self.cloud_tracker.step(sub_df.tail(20), dt=dt_phys, steps=15)
                        if density is not None:
                            density = np.convolve(density, kernel, mode='same')
                            
                            # Gamma 2.0 Deep Incandescence (v71.1)
                            # v37.2: Lush Nebula Polarity Mapping
                            # Usamos o Delta Field (Polaridade) escalado pela densidade para o hex
                            delta_scaled = np.nan_to_num(self.cloud_tracker.delta_field) * density
                            
                            # Normalização e Gamma
                            max_val = np.max(np.abs(delta_scaled)) + 1e-9
                            # Normalização simétrica em [-1, 1]
                            norm_delta = np.clip(delta_scaled / max_val, -1.0, 1.0)
                            # Aplica Gamma preservando o sinal
                            gamma_delta = np.sign(norm_delta) * np.power(np.abs(norm_delta), 0.5)
                            
                            # Codificação Hex: 00-49 (Sell/Magenta), 50 (Neutral), 51-99 (Buy/Cyan)
                            # Transformamos [-1, 1] em [0, 99] onde 50 é o zero
                            s_hex = "".join([f"{int(50 + d*49):02d}" for d in gamma_delta])
                            self.cloud_trail.insert(0, f"{w_p_min:.2f}|{w_p_max:.2f}|{s_hex}")
                    print(f"✅ Q-MATH :: Campo Espectral v71.1 Materializado.")

            if self.lbm_tracker is None: self.lbm_tracker = LBMFluidDynamics(df['low'].min()-300, df['high'].max()+300, 200, smagorinsky_cs=0.15)
            if self.plasma_tracker is None: self.plasma_tracker = PlasmaMarketTracker()
            if self.rmt_tracker is None: self.rmt_tracker = RandomMatrixTracker(100)
            if self.qcd_tracker is None: self.qcd_tracker = MarketQCDTracker(20)
            if self.rht_tracker is None: self.rht_tracker = LiveRHTTracker(self.current_symbol, 300)
            if self.qrw_tracker is None: self.qrw_tracker = QRWTracker(401)
            if self.precog_node is None: self.precog_node = QuantumPreCognitionNode(self.current_symbol)

            def run_schrodinger():
                try:
                    curr_time = df.iloc[-1]['time']
                    pti = getattr(self, "current_pti_context", 0.0)
                    dt_phys = 2.0
                    
                    # Dynamics in Absolute Space v71.1
                    self.cloud_tracker.price_min = p_min
                    self.cloud_tracker.price_max = p_max
                    
                    density, _ = self.cloud_tracker.step(df.tail(20), dt=dt_phys, steps=15, pti=pti)
                    if density is not None:
                        # 31-point Gaseous Blur (v71.0)
                        kernel = np.ones(31) / 31.0
                        density = np.convolve(density, kernel, mode='same')
                        
                        # Gamma 2.0 + HDR Overdrive Scaling (v71.0)
                        # v37.2: Lush Nebula Polarity Mapping (Real-Time)
                        delta_scaled = np.nan_to_num(self.cloud_tracker.delta_field) * density
                        max_val = np.max(np.abs(delta_scaled)) + 1e-9
                        norm_delta = np.clip(delta_scaled / max_val, -1.0, 1.0)
                        gamma_delta = np.sign(norm_delta) * np.power(np.abs(norm_delta), 0.5)
                        
                        snapshot_hex = "".join([f"{int(50 + d*49):02d}" for d in gamma_delta])
                        slice_data = f"{p_min:.2f}|{p_max:.2f}|{snapshot_hex}"
                        
                        if self.last_physics_time is None or curr_time > self.last_physics_time:
                            self.cloud_trail.insert(0, slice_data)
                            if len(self.cloud_trail) > 801: self.cloud_trail.pop()
                            self.last_physics_time = curr_time
                        else:
                            if self.cloud_trail: self.cloud_trail[0] = slice_data
                        
                        return {"cloud_str": "^".join(self.cloud_trail)}
                    return {"cloud_str": "0.0:0.0:0.0:"}
                except Exception as e: return {"cloud_str": f"ERROR:{str(e)}"}
                
            def run_lbm():
                try:
                    l_den, l_vel, l_press, l_rey = self.lbm_tracker.process_tick_stream(df.tail(5), steps=2)
                    lbm_sig = self.lbm_tracker.detect_squeeze_rupture(df.tail(150), l_den, l_vel, l_press, l_rey, current_regime=self.current_regime_context)
                    return {"lbm_signal": lbm_sig}
                except Exception as e:
                    return {"lbm_signal": "LAMINAR_FLOW"}

            def run_plasma():
                try:
                    # [v3.0] Magnetohydrodynamics (MHD Ideal)
                    zones = self.plasma_tracker.scan_for_plasma_zones(df.tail(150))
                    curr_c = df.iloc[-1]
                    prev_c = df.iloc[-2] if len(df) > 1 else curr_c
                    stability, sig, metrics = self.plasma_tracker.process_tick(curr_c, prev_c, zones, dt=0.01)
                    
                    return {
                        "z_pinch_signal": sig,
                        "mhd_stability": stability,
                        "mhd_beta": metrics.get('beta', 1.0)
                    }
                except Exception as e:
                    return {"z_pinch_signal": "NEUTRAL", "mhd_stability": 100.0, "mhd_beta": 1.0}

            def run_rmt():
                try:
                    # Necessita o velocity array do LBM, mas se for assíncrono passamos None e ele ignora
                    rmt_sig = self.rmt_tracker.process_spectral_filter(df.tail(150), None)
                    return {"rmt_signal": rmt_sig}
                except Exception as e:
                    return {"rmt_signal": "NOISE_DOMINANT"}

            def run_qrw():
                try:
                    pti = getattr(self, "current_pti_context", 0.0)
                    # [v2.5] Quantum Random Walk (Stateful ASI-5)
                    # Usamos o momentum do PTI para acoplamento de massa
                    res = self.qrw_tracker.project_future_horizon(df.tail(100), steps=6)
                    qrw_sig = res.get("bias", "NEUTRAL")
                    
                    # Extração da distribuição para o histórico (Heatmap)
                    dist = res.get("distribution", np.array([]))
                    s_hex = "0"
                    if len(dist) > 0:
                        # Selecionamos picos para o histórico resumido (MT5)
                        v_max = np.max(dist) + 1e-9
                        norm_dist = np.clip(dist / v_max, 0, 1.0)
                        # Amostragem de 50 pontos para o gráfico histórico
                        indices = np.linspace(0, len(norm_dist)-1, 50, dtype=int)
                        s_hex = "".join([f"{int(norm_dist[i]*99):02d}" for i in indices])

                    return {
                        "qrw_signal": qrw_sig,
                        "qrw_skew": self.qrw_tracker.engine.get_skewness() if self.qrw_tracker.engine else 0.0,
                        "qrw_history": s_hex
                    }
                except Exception as e:
                    return {"qrw_signal": "NEUTRAL", "qrw_skew": 0.0, "qrw_history": "0"}

            with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
                f_sch = executor.submit(run_schrodinger)
                f_lbm = executor.submit(run_lbm)
                f_pla = executor.submit(run_plasma)
                f_rmt = executor.submit(run_rmt)
                f_qrw = executor.submit(run_qrw)
                results = f_sch.result()
                results.update(f_lbm.result())
                results.update(f_pla.result())
                results.update(f_rmt.result())
                results.update(f_qrw.result())

            with self.state_lock:
                self.current_state.update({
                    "status": "ACTIVE", "latest_price": current_close,
                    "cloud_str": results.get("cloud_str", ""),
                    "lbm_signal": results.get("lbm_signal", "LAMINAR_FLOW"),
                    "rmt_signal": results.get("rmt_signal", "NOISE_DOMINANT"),
                    "qrw_signal": results.get("qrw_signal", "NEUTRAL"),
                    "qrw_skew": results.get("qrw_skew", 0.0),
                    "qrw_history": results.get("qrw_history", "0"),
                    "z_pinch_signal": results.get("z_pinch_signal", "NEUTRAL"),
                    "mhd_stability": results.get("mhd_stability", 100.0)
                })
        except Exception as e: print(f"❌ Q-MATH :: Error: {e}")

    def run_subscriber_loop(self):
        last_heartbeat = time.time()
        while self.is_running:
            latest = None
            if time.time() - last_heartbeat > 10:
                print(f"💓 Q-MATH :: Coração Batendo. Aguardando sinal em {PORT_TICK_FEED}...")
                last_heartbeat = time.time()
                
            while True:
                try:
                    msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                    if msg[0].decode('utf-8') == TOPIC_MARKET_BAR: 
                        latest = pickle.loads(msg[1])
                        last_heartbeat = time.time() # Reset heartbeat on data
                except zmq.Again: break
                except Exception: break
            if latest: self.process_market_data(latest)
            else: time.sleep(0.01)

    def run_reply_server(self):
        poller = zmq.Poller()
        poller.register(self.rep_socket, zmq.POLLIN)
        while self.is_running:
            try:
                socks = dict(poller.poll(1000))
                if self.rep_socket in socks:
                    msg = self.rep_socket.recv().decode('utf-8').split("|")
                    if len(msg) >= 2: self.current_regime_context = int(msg[1])
                    if len(msg) >= 3: self.current_pti_context = float(msg[2])
                    with self.state_lock: reply = pickle.dumps(self.current_state)
                    self.rep_socket.send(reply)
            except Exception as e: 
                print(f"❌ Q-MATH :: Reply Server Error: {e}")
                time.sleep(0.1)

    def startup(self):
        self.is_running = True
        print("🚀 Q-MATH :: Booting Relative Surface Engine...")
        if not mt5.initialize(): print("❌ Q-MATH :: MT5 Error.")
        threading.Thread(target=self.run_subscriber_loop, daemon=True).start()
        self.run_reply_server()

    def shutdown(self):
        self.is_running = False; self.sub_socket.close(); self.rep_socket.close(); mt5.shutdown()

if __name__ == "__main__":
    node = QMathNode(); node.startup()
