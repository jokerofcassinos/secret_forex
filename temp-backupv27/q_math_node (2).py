"""
Q-MATH NODE (ZMQ SUB / REP Node - v69.0)
Função: Singularity Convergence (v69.0).
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
        print("⚛️ Q-MATH :: Sincronizando subsistemas [ABSOLUTE INERTIAL v53.2]...")
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
            # [v66.0] Spectral Nebula Engine - Absolute Reference Manifold
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
                print(f"⚛️ Q-MATH :: Singularity Glow Engine v68.0 Iniciado em {payload_sym}.")
                
                # [SINGULARITY WARM-UP] v69.0 Spectral Grain (21pt Blur)
                warmup_size = min(40, len(df) - 11)
                if warmup_size > 0:
                    print(f"🚀 Q-MATH :: Materializando Vapor Espectral ({warmup_size} snapshots)...")
                    kernel = np.ones(21) / 21.0
                    for i in range(len(df) - warmup_size, len(df)):
                        sub_df = df.iloc[:i+1].copy()
                        c_close = sub_df['close'].iloc[-1]
                        
                        # [v69.0] Hot Core Physics: dt=2.0, steps=15
                        dt_phys = 2.0
                        
                        # Absolute Space Physics (v69.0)
                        density, _ = self.cloud_tracker.step(sub_df.tail(20), dt=dt_phys, steps=15)
                        if density is not None:
                            density = np.convolve(density, kernel, mode='same')
                            
                            # Gamma 1.6 Balanced Core (v69.0)
                            gamma_den = np.power(density, 1.6)
                            # Normalization (v69.0)
                            v_max = np.max(gamma_den) * 0.9
                            gamma_den = np.clip(gamma_den / (v_max + 1e-9), 0, 1.0)
                            
                            s_hex = "".join([f"{int(d*99):02d}" for d in gamma_den])
                            # Payload v69: p_min|p_max|hex
                            self.cloud_trail.insert(0, f"{p_min:.2f}|{p_max:.2f}|{s_hex}")
                    print(f"✅ Q-MATH :: Campo Espectral v69.0 Materializado.")

            if self.lbm_tracker is None: self.lbm_tracker = LBMFluidDynamics(df['low'].min()-100, df['high'].max()+100, 200, tau=1.0)
            if self.plasma_tracker is None: self.plasma_tracker = PlasmaMarketTracker()
            if self.rmt_tracker is None: self.rmt_tracker = RandomMatrixTracker(100)
            if self.qrw_tracker is None:
                try: 
                    import qrw_engine
                    self.qrw_engine_core = qrw_engine.QRWEngine(401)
                    self.qrw_tracker = type('obj', (object,), {'last_history': [], 'engine': self.qrw_engine_core})
                except Exception as e: 
                    print(f"⚠️ Q-MATH :: QRW Engine fail: {e}")
                    self.qrw_tracker = type('obj', (object,), {'last_history': [], 'engine': None})
            if self.qcd_tracker is None: self.qcd_tracker = MarketQCDTracker(20)
            if self.rht_tracker is None: self.rht_tracker = LiveRHTTracker(self.current_symbol, 300)
            if self.precog_node is None: self.precog_node = QuantumPreCognitionNode(self.current_symbol)

            def run_schrodinger():
                try:
                    curr_time = df.iloc[-1]['time']
                    pti = getattr(self, "current_pti_context", 0.0)
                    
                    # [V69.0] Spectral Synthesis - Absolute Price Space
                    dt_phys = 2.0
                    
                    # Dynamics in Absolute Space v69.0
                    density, _ = self.cloud_tracker.step(df.tail(20), dt=dt_phys, steps=15, pti=pti)
                    if density is not None:
                        # 21-point Whispy Grain (v69.0)
                        kernel = np.ones(21) / 21.0
                        density = np.convolve(density, kernel, mode='same')
                        
                        # Gamma 1.6 + Peak Scaling (v69.0)
                        gamma_den = np.power(density, 1.6)
                        v_max = np.max(gamma_den) * 0.9
                        gamma_den = np.clip(gamma_den / (v_max + 1e-9), 0, 1.0)
                        
                        snapshot_hex = "".join([f"{int(d*99):02d}" for d in gamma_den])
                        # Payload v69: p_min|p_max|hex
                        slice_data = f"{p_min:.2f}|{p_max:.2f}|{snapshot_hex}"
                        
                        if self.last_physics_time is None or curr_time > self.last_physics_time:
                            self.cloud_trail.insert(0, slice_data)
                            if len(self.cloud_trail) > 41: self.cloud_trail.pop()
                            self.last_physics_time = curr_time
                        else:
                            if self.cloud_trail: self.cloud_trail[0] = slice_data
                        
                        return {"cloud_str": "^".join(self.cloud_trail)}
                    return {"cloud_str": "0.0:0.0:0.0:"}
                except Exception as e: return {"cloud_str": f"ERROR:{str(e)}"}

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                f_sch = executor.submit(run_schrodinger)
                results = f_sch.result()

            with self.state_lock:
                self.current_state.update({
                    "status": "ACTIVE", "latest_price": current_close,
                    "cloud_str": results.get("cloud_str", "")
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
