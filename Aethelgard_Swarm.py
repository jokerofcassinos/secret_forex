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
import MetaTrader5 as mt5
import logging

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
from Code.N_Core.quantum_oracle import QuantumOracle
from Code.N_Core.yield_governor import YieldGovernor
from Code.N_Core.live_rht import LiveRHTTracker
from Code.N_Core.market_qcd import MarketQCDTracker
from Code.N_Core.quantum_projection import QuantumPreCognitionNode
from Code.N_Core.tensor_network import TensorNetworkNode
from Code.N_Core.quantum_tunneling import QuantumTunnelingNode
from Code.N_Core.quantum_oscillator import QuantumOscillatorNode
from Code.N_Core.quantum_glass import QuantumGlassNode
from Code.N_Core.quantum_setups import QuantumSetupEngine
from Code.N_Core.virtual_neural_zones import AdaptiveNeuralZones



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
                    params = req_str.split("GET /nexus?")[1].split(" ")[0]
                    if "tf=" in params:
                        current_mt5_tf = int(params.split("tf=")[1].split("&")[0])
                    if "symbol=" in params:
                        new_symbol = params.split("symbol=")[1].split("&")[0]
                        if new_symbol != getattr(run_tcp_server, "current_mt5_symbol", None):
                            run_tcp_server.current_mt5_symbol = new_symbol
                            print(f"📡 SWARM :: Símbolo alterado para: {new_symbol}")
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
    def __init__(self, symbol=None):
        self.symbol = symbol
        self.bridge = MT5NeuralBridge(symbol)
        self.q_logic = QuantumIndicators()
        self.rht_tracker = LiveRHTTracker(symbol, lookback=300)
        self.oracle = QuantumOracle(simulations=5000)
        self.yield_governor = YieldGovernor(danger_window=30, danger_threshold=25.0)
        self.pre_cognition = QuantumPreCognitionNode(symbol=self.symbol)
        self.tensor_network = TensorNetworkNode()
        self.qte_engine = QuantumTunnelingNode()
        self.qho_engine = QuantumOscillatorNode()
        self.qgc_node = QuantumGlassNode()
        self.setup_engine = QuantumSetupEngine()
        self.anz_engine = AdaptiveNeuralZones()
        
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
        self.setup_cache = []
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
        print(f"--- INICIANDO MOTOR SWARM v4.0 [SINGULARITY BOOT] ---")
        # Inicia o servidor TCP independente do símbolo (Ouvido do Observador)
        threading.Thread(target=run_tcp_server, daemon=True).start()
        
        if self.symbol:
            print(f"📡 SWARM :: Realidade definida para: {self.symbol}")
            if not self.bridge.initialize(): return False
        else:
            print("📡 SWARM :: Estado de Superposição Ativo. Aguardando observação do gráfico...")
            if not mt5.initialize(): 
                print("❌ SWARM :: Falha ao inicializar MT5 em Modo Agnóstico.")
                return False
            
        self.is_running = True
        # Normalização de Símbolo (Resolve sufixos como .m ou .raw)
        if self.symbol:
            sym_info = mt5.symbol_info(self.symbol)
            if sym_info:
                self.symbol = sym_info.name
                print(f"📡 SWARM :: Símbolo normalizado para: {self.symbol}")
            else:
                print(f"⚠️ SWARM :: Falha ao normalizar {self.symbol}. Verifique se o ativo está no Market Watch.")

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
        
        from Code.N_Core.quantum_oscillator import QuantumOscillatorNode
        qho_boot = QuantumOscillatorNode()
        
        from Code.N_Core.quantum_setups import QuantumSetupEngine
        setup_boot = QuantumSetupEngine()
        
        self.regimes_cache = []
        self.signals_cache = []
        self.lbm_cache = []
        self.z_pinch_cache = []
        self.qrw_cache = []
        self.qcd_cache = []
        self.cyt_danger_cache = []
        self.sec_cache = []
        self.setup_cache = []
        
        scores_hist = []
        self.prev_s, self.prev_c = 0, 0
        
        for i in range(len(df)):
            if i < window_calc:
                self.regimes_cache.append("0|0")
                self.signals_cache.append("0")
                self.lbm_cache.append("0")
                self.z_pinch_cache.append("0")
                self.qrw_cache.append("0")
                self.setup_cache.append("0")
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
            
            # --- SETUP ENGINE BACKFILL ---
            try:
                qho_h = qho_boot.calculate_quantum_state(slice_df)
                ricci_h_val = 0.0
                if has_cpp_hist:
                    try: ricci_h_val = float(def_arr[-1]) if len(def_arr) > 0 else 0.0
                    except: pass
                lbm_sig_str = "LAMINAR_FLOW"
                if lbm_sig_hist == "1": lbm_sig_str = "FLUID_RUPTURE_BULL"
                elif lbm_sig_hist == "2": lbm_sig_str = "FLUID_RUPTURE_BEAR"
                elif lbm_sig_hist == "3": lbm_sig_str = "BOSONIC_SQUEEZE"
                
                qcd_sig_str = "CONFINED"
                if "FISSION_EXPANSION_UP" in qcd_sig: qcd_sig_str = "FISSION_EXPANSION_UP"
                elif "FISSION_EXPANSION_DOWN" in qcd_sig: qcd_sig_str = "FISSION_EXPANSION_DOWN"
                
                setup_ctx_h = {
                    "regime": r_score, "conf": conf, "prev_regime": scores_hist[-2] if len(scores_hist) > 1 else 0,
                    "lbm_signal": lbm_sig_str, "qcd_signal": qcd_sig_str,
                    "rht_flash": 0.0, "rmt_signal": "NOISE_x1.0",
                    "qrw_signal": "NEUTRAL", "z_pinch_signal": "NEUTRAL",
                    "qgc_pull": 0.0, "qho_n": qho_h.get('n', 0), "qho_status": qho_h.get('status', ''),
                    "qte_prob": 0.0, "qte_advice": "STABLE_ORBIT",
                    "qdd_fidelity": 0.0, "ricci": ricci_h_val,
                    "is_collapsed": False, "sec_metrics": None,
                }
                hist_setups = setup_boot.evaluate(setup_ctx_h, backfill=True)
                if hist_setups:
                    best = max(hist_setups, key=lambda s: s.get('confidence', 0))
                    # Encode: setup number (1-7) * direction sign
                    snum = int(best['setup'][1])  # S1..S7 → 1..7
                    sdir = 1 if best['direction'] == 'LONG' else -1
                    self.setup_cache.append(str(snum * sdir))
                else:
                    self.setup_cache.append("0")
            except Exception:
                self.setup_cache.append("0")
            
            if i == len(df) - 1 and has_cpp_hist:
                try:
                    q_slc = df.tail(500)
                    m_thr = q_slc['tick_volume'].mean() * 2.0
                    res = qgc_hist.compute_hawking_decay(q_slc['close'].values, q_slc['tick_volume'].values, q_slc['atr_static'].fillna(0).values, m_thr)
                    q_parts = [f"{int(a)}|{p:.2f}|{min(10.0, (m/m_thr)*2):.1f}" for m, p, a in zip(res.get("residual_masses", []), res.get("centers_of_mass", []), res.get("ages", [])) if m > 0]
                    self.qgc_data_str = ",".join(q_parts)
                except: pass
        
        # Tactical: Dots disabled, QCD and MSNR now fully historical
        self.dots_cache = ["0"] * len(df)

        self.last_time = df.iloc[-1]['time']
        self.rht_cache = ["0"] * 300
        setup_count = sum(1 for x in self.setup_cache if x != '0')
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot N-Core Concluído. {sum(1 for x in self.qcd_cache if x != '0')} QCD, {setup_count} Setup signals restored.")

    def live_evolution_loop(self):
        global nexus_data_str, current_mt5_tf
        print("🧠 SWARM CORE :: Loop Evolutivo Iniciado.")
        try:
            while self.is_running:
                # 1. SINCRONIZAÇÃO DE SÍMBOLO E TIMEFRAME (SINGULARIDADE)
                mt5_sym = getattr(run_tcp_server, "current_mt5_symbol", self.symbol)
                
                # Se não há símbolo definido nem no MT5 nem no Swarm, aguarda colapso da função de onda
                if mt5_sym is None:
                    time.sleep(1)
                    continue

                # Sintonização Inicial ou Mudança Detectada
                if self.symbol is None or mt5_sym != self.symbol or (current_mt5_tf is not None and self.active_tf != current_mt5_tf):
                    print(f"📡 SWARM :: {'Sintonização Inicial' if self.symbol is None else 'Salto Dimensional'} detectado! Símbolo: {mt5_sym} | TF: {current_mt5_tf}")
                    
                    self.symbol = mt5_sym
                    self.active_tf = current_mt5_tf if current_mt5_tf is not None else self.active_tf
                    
                    # Atualiza pontes e trackers
                    self.bridge.symbol = self.symbol
                    self.bridge.initialize()
                    self.rht_tracker.symbol = self.symbol
                    self.pre_cognition.symbol = self.symbol
                    
                    self.regimes_cache.clear(); self.sec_cache.clear(); self.dots_cache.clear()
                    self.qcd_cache.clear(); self.cyt_danger_cache.clear(); self.last_time = 0
                    
                    ctrl_payload = pickle.dumps({"action": "CHANGE_TF", "timeframe": self.active_tf, "symbol": self.symbol})
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
                        # 1. CÁLCULO DE MÉTRICAS BASE (FALLBACK MULTI-CAMADA)
                        tick = mt5.symbol_info_tick(self.symbol)
                        current_price = tick.last if (tick is not None and tick.last > 0) else df['close'].iloc[-1]
                        
                        # Garantia de IFV não-zero
                        inst_avg = current_price if current_price > 0 else df['close'].mean()
                        if inst_avg <= 0:
                            logging.error("Critical failure in inst_avg calculation. Falling back to last record.")
                            inst_avg = df['close'].tail(1).values[0] # Último esforço
                        
                        # 2. ANÁLISE DO HEATMAP DE SCHRÖDINGER
                        cloud_data = q_state.get('cloud_str', "")
                        cloud_status = "DECOHERENCE"
                        cloud_dens_val = 0.0
                        if ":" in cloud_data:
                            try:
                                densities = [float(p.split('|')[1]) for p in cloud_data.split(':')[1].split(',') if '|' in p]
                                if densities:
                                    # Aplicamos um Ganho Quântico (x10) para sensibilizar a leitura no regime de 80k
                                    cloud_dens_val = min(1.0, max(densities) * 10.0) 
                                    # Trava de Status em 0.005 para ativação imediata no regime 80k
                                    cloud_status = "DENSITY_LOCKED" if cloud_dens_val > 0.005 else "SCANNING"
                            except Exception: pass
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
                        if len(self.setup_cache) > 0: self.setup_cache.pop(0)
                        self.setup_cache.append("0")
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
                    # Saneamento de Sinais Quânticos (Evita erros de serialização de objetos)
                    def sanitize_signal(val):
                        if hasattr(val, '__name__'): return str(val.__name__)
                        if "engine" in str(val).lower(): return "NEUTRAL"
                        return str(val)

                    # Bypass Tático: Passagem direta de sinais quânticos para evitar sanitização errônea
                    qrw_h = q_state.get("qrw_history", "0")
                    qrw_s = q_state.get("qrw_signal", "NEUTRAL")
                    rmt_s = sanitize_signal(q_state.get("rmt_signal", "NEUTRAL"))
                    z_p_s = q_state.get("z_pinch_signal", "NEUTRAL")

                    # Fail-Safe AdS/CFT: Se Ricci for alto, força ativação de Bulk se estiver Neutral
                    if z_p_s == "NEUTRAL" and ricci_c > 0.8:
                        z_p_s = "Z_PINCH_PLASMA_BULL" if r_score == 1 else "Z_PINCH_PLASMA_BEAR"
                    
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

                    rht_f = q_state.get("rht_flash", 0.0)
                    rht_fh = q_state.get("rht_flash_history", "")
                    # 8. GESTÃO DE SINGULARIDADE (R-EXEC)
                    # Calcula o Horizonte de Singularidade e atualiza os SLs no MT5
                    tr_recent = (df['high'] - df['low']).tail(14).mean()
                    precog_res = self.pre_cognition.project_containment_horizon(df, df['close'].iloc[-1], tr_recent)
                    
                    self.bridge.thermodynamic_sl_tp(
                        r_score, 
                        df['close'].iloc[-1], 
                        tr_recent, 
                        None, # plasma_zones removido, usando PreCog
                        q_state.get("cloud_prob", None), 
                        None, # Cloud Tracker Passivo
                        precog_res
                    )
                    
                    # 3. EXTRAÇÃO MULTI-TIMEFRAME PARA QDD
                    sync_data = self.bridge.fetch_sync_multi_tf(count=self.tensor_network.lookback + 20)
                    qdd_fidelity = self.tensor_network.calculate_global_alignment(sync_data)
                    
                    # 4. CÁLCULO DE TUNELAMENTO (QTE - TAKE PROFIT QUÂNTICO)
                    # Sincronização: O Q-Math envia como 'cloud_prob'
                    q_density = q_state.get("cloud_prob", [])
                    qte_prob = self.qte_engine.calculate_exit_probability(df, df['close'].iloc[-1], q_density)
                    qte_advice = self.qte_engine.get_tp_advice(qte_prob)
                    
                    # 5. CÁLCULO DE OSCILAÇÃO (QHO - ESTABILIDADE QUÂNTICA)
                    qho_state = self.qho_engine.calculate_quantum_state(df)
                    qho_shells = ",".join([f"{p:.2f}" for p in qho_state.get('shells', [])])
                    
                    # 6. CÁLCULO DE GRAVIDADE (QGC - REAL TIME SCAN)
                    self.qgc_node.scan_for_condensates(df)
                    qgc_tel = self.qgc_node.get_gravity_telemetry(df['close'].iloc[-1])
                    
                    # 7. MAGNETOHYDRODYNAMICS (MHD - FIELD STRENGTH)
                    mhd_field = (df['close'].diff().rolling(14).std() / (df['tick_volume'].rolling(14).mean() + 1e-9)).iloc[-1]
                    mhd_strength = min(10.0, mhd_field * 100000)
                    
                    # Formata as zonas QGC para o MT5: "age|price|mass"
                    q_parts = []
                    for z in qgc_tel['active_zones']:
                        v_mass = max(2.0, z.get('mass', 2.0) * 1.5)
                        z_age = int(z.get('age', 0))
                        q_parts.append(f"{z_age}|{z.get('price', 0.0):.2f}|{v_mass:.2f}")
                    
                    self.qgc_data_str = ",".join(q_parts)

                    # 8. QUANTUM SETUP ENGINE (Hybrid Execution Setups)
                    setup_ctx = {
                        "regime": r_score, "conf": conf, "prev_regime": self.prev_s,
                        "lbm_signal": lbm_s, "qcd_signal": qcd_s,
                        "rht_flash": rht_f, "rmt_signal": rmt_s,
                        "qrw_signal": qrw_s, "z_pinch_signal": z_p_s,
                        "qgc_pull": qgc_tel.get('gravity_pull', 0.0),
                        "qho_n": qho_state.get('n', 0), "qho_status": qho_state.get('status', ''),
                        "qho_shells": qho_state.get('shells', []), "atr": df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min() if len(df) > 20 else 10.0,
                        "qte_prob": qte_prob, "qte_advice": qte_advice,
                        "qdd_fidelity": qdd_fidelity, "ricci": ricci_c,
                        "is_collapsed": q_state.get("is_collapsed", False),
                        "sec_metrics": q_state.get("sec_metrics"),
                        "ksi_val": q_state.get("ksi_val", 0.0),
                        "precog_sl_long": q_state.get("precog_sl_long", df['close'].iloc[-1] - 30.0),
                        "precog_sl_short": q_state.get("precog_sl_short", df['close'].iloc[-1] + 30.0),
                    }
                    active_setups = self.setup_engine.evaluate(setup_ctx)
                    
                    # 9. ADAPTIVE NEURAL ZONES (ANZ) - Gestão de Risco Híbrida
                    # Sincroniza posições REAIS do MT5 para a ANZ
                    live_positions = mt5.positions_get(symbol=self.symbol)
                    live_tickets = []
                    if live_positions:
                        for p in live_positions:
                            tkt_str = str(p.ticket)
                            live_tickets.append(tkt_str)
                            if tkt_str not in self.anz_engine.active_positions:
                                p_dir = "LONG" if p.type == mt5.ORDER_TYPE_BUY else "SHORT"
                                # Ordens manuais recebem S1 (Gestão Absoluta PreCog + QTE)
                                self.anz_engine.register_position(tkt_str, "S1_GRAVITATIONAL_SLINGSHOT", p_dir, p.price_open)
                    
                    # Remove posições reais que já foram fechadas no MT5
                    for tkt in list(self.anz_engine.active_positions.keys()):
                        if not tkt.startswith("virt_") and tkt not in live_tickets:
                            del self.anz_engine.active_positions[tkt]

                    # Se um setup novo disparar, registra na ANZ para acompanhamento virtual
                    if active_setups:
                        best = self.setup_engine.get_strongest_signal()
                        if best:
                            ticket = f"virt_{int(time.time())}"
                            self.anz_engine.register_position(ticket, best['setup'], best['direction'], df['close'].iloc[-1])
                    
                    # Avalia as zonas de todas as posições ativas
                    anz_zones = self.anz_engine.evaluate_zones(setup_ctx, df['close'].iloc[-1])
                    
                    # Remove posições que mandaram fechar (Virtual Exit ou Real Exit)
                    to_remove = []
                    for tkt, zone in anz_zones.items():
                        if zone["action"] != "HOLD":
                            to_remove.append(tkt)
                            print(f"🛑 ANZ :: ORDEM COLAPSADA ({tkt}) -> {zone['action']} | SL:{zone['sl']:.2f}")
                            if not tkt.startswith("virt_"):
                                # É uma ordem real! Fecha no MT5 via bridge
                                is_buy = self.anz_engine.active_positions[tkt]["direction"] == "LONG"
                                self.bridge.close_position(int(tkt), is_buy)
                                
                    for tkt in to_remove:
                        if tkt in self.anz_engine.active_positions:
                            del self.anz_engine.active_positions[tkt]
                        
                    setup_tel_base = self.setup_engine.format_telemetry()
                    # Adiciona a primeira zona ativa (se existir) para plotagem visual no HUD
                    if anz_zones:
                        first_zone = list(anz_zones.values())[0]
                        setup_tel = f"{setup_tel_base}|{float(first_zone['sl']):.2f}|{float(first_zone['tp']):.2f}"
                        print(f"📡 ANZ PAYLOAD: {setup_tel}")
                    else:
                        setup_tel = f"{setup_tel_base}|0.00|0.00"

                    # Cache de setup histórico (live update in-place)
                    current_setup_val = "0"
                    if active_setups:
                        best = max(active_setups, key=lambda s: s.get('confidence', 0))
                        snum = int(best['setup'][1])
                        sdir = 1 if best['direction'] == 'LONG' else -1
                        current_setup_val = str(snum * sdir)
                        for s in active_setups:
                            print(f"⚡ SETUP ATIVO: {s['setup']} → {s['direction']} (Confiança: {s['confidence']})")
                            
                    if len(self.setup_cache) > 0:
                        self.setup_cache[-1] = current_setup_val
                    else:
                        self.setup_cache.append(current_setup_val)

                    # 9. CONSULTA À FÍSICA (REQ-REP)
                    # Verifica colapso topológico ou quebra física do SL Virtual
                    self.bridge.enforce_quantum_boundary(df, None, None, q_state.get("is_collapsed", False))

                    # [FULL TELEMETRY + HEATMAP ANALYSIS]
                    nexus_data_str = f"0;0;{status_final};0;{','.join(self.regimes_cache)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{q_state.get('cloud_str')};{lbm_s};{z_p_s};{rmt_s};{qrw_s};{','.join(self.lbm_cache)};{ricci_c:.4f};{h_ent:.4f};{','.join(self.cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_s};{coll_s};{qcd_s};{','.join(self.qcd_cache)};{self.qgc_data_str};{w_str};{qrw_h};{rht_h};{rht_f};{rht_fh};{qdd_fidelity:.4f};{qte_prob:.4f};{qte_advice};{qho_state.get('n')};{qho_state.get('stability'):.4f};{qho_state.get('status')};{qho_shells};{mhd_strength:.4f};{setup_tel};{','.join(self.setup_cache)}"
                else: time.sleep(0.01)
        except KeyboardInterrupt: self.shutdown()

    def shutdown(self):
        self.is_running = False
        self.sub_socket.close(); self.req_socket.close()
        self.sub_context.term(); self.req_context.term()
        print("\n🧠 SWARM CORE :: Desligado.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Aethelgard Swarm - AGI Core")
    parser.add_argument('--asset', type=str, default=None, help='Ativo para operação (Se None, aguarda sinal do MT5)')
    args = parser.parse_args()
    
    # Se não for passado --asset, a máquina inicia em modo agnóstico (Aguardando Observador)
    agi = AethelgardSwarm(symbol=args.asset)
    if agi.startup(): agi.live_evolution_loop()
