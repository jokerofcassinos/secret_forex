"""
Q-MATH NODE (ZMQ SUB / REP Node - v2.1)

Função: Assina (SUB) os dados de mercado do NEXUS ROUTER.
Atualiza em background todos os trackers pesados de C++ (LBM, Schrödinger, RMT).
Levanta um servidor (REP) para que o AGI_CORE consulte os dados calculados instantaneamente.
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

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++
if os.name == 'nt':
    # [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++ na ROOT
    root_path = os.path.dirname(__file__)
    if os.path.exists(root_path):
        os.add_dll_directory(root_path)
        if root_path not in sys.path:
            sys.path.insert(0, root_path)

    # Mingw64 Fallback
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")



from Code.N_Core.swarm_bus import create_subscriber, create_reply_server, PORT_TICK_FEED, PORT_Q_MATH, TOPIC_MARKET_BAR

# Trackers C++ / Física Pesada
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
        # Comunicação SUB (Ouve o mercado)
        self.sub_context, self.sub_socket = create_subscriber(PORT_TICK_FEED, TOPIC_MARKET_BAR)
        
        # Comunicação REP (Responde ao AGI Core)
        self.rep_context, self.rep_socket = create_reply_server(PORT_Q_MATH)
        
        self.is_running = False
        
        # Trackers Locais
        self.cloud_tracker = None
        self.lbm_tracker = None
        self.plasma_tracker = None
        self.rmt_tracker = None
        self.qrw_tracker = None
        self.qcd_tracker = None
        self.rht_tracker = None
        self.cyt = cyt_engine.CYTEngine()
        self.ksi_engine = None
        self.precog_node = None
        
        # Estado atual cacheado para responder rapidamente
        self.current_state = {
            "status": "INITIALIZING",
            "lbm_zones": [],
            "cloud_zones": [],
            "rmt_signal": 0.0,
            "qrw_density": [],
            "qcd_signal": "CONFINED",
            "rht_status": "PURIFYING",
            "rht_history": [],
            "ricci_curvature": 0.0
        }
        
        # Trava para evitar conflito de leitura/escrita no estado interno
        self.state_lock = threading.Lock()

    def process_market_data(self, payload):
        """Processa o pacote recebido e atualiza os motores C++ EM PARALELO"""
        try:
            df = payload.get("data")
            tf = payload.get("timeframe")
            payload_sym = payload.get("symbol", getattr(self, "current_symbol", None))

            # Se mudou o timeframe ou símbolo, destroi a física antiga para resetar
            if (tf is not None and getattr(self, "active_tf", None) != tf) or (getattr(self, "last_processed_symbol", None) != payload_sym):
                print(f"\n⚛️ Q-MATH :: Salto Dimensional Detectado. Recriando física para {payload_sym} TF: {tf}")
                self.active_tf = tf
                self.last_processed_symbol = payload_sym
                self.current_symbol = payload_sym # Sincroniza o símbolo
                
                self.cloud_tracker = None
                self.lbm_tracker = None
                self.plasma_tracker = None
                self.rmt_tracker = None
                self.qrw_tracker = None
                self.rht_tracker = None

            # Inicializações Lazy (só ocorrem quando chegam os primeiros dados)
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

            if self.rmt_tracker is None:
                self.rmt_tracker = RandomMatrixTracker(time_steps=100)
                
            if self.qrw_tracker is None:
                try:
                    import qrw_engine
                    # Injeção Direta: Bypass de camada para evitar conflitos de nome
                    self.qrw_engine_core = qrw_engine.QRWEngine(401)
                    self.qrw_tracker = type('obj', (object,), {'last_history': [], 'engine': self.qrw_engine_core})
                except Exception as e:
                    print(f"❌ Q-MATH :: Erro Crítico no Motor QRW: {e}")
                    self.qrw_tracker = type('obj', (object,), {'last_history': [], 'engine': None})
                
            if self.qcd_tracker is None:
                self.qcd_tracker = MarketQCDTracker(lookback_window=20)
                
            if self.rht_tracker is None:
                # O símbolo agora vem do payload do roteador, não dos attrs do df
                self.rht_tracker = LiveRHTTracker(symbol=getattr(self, "current_symbol", "GER40.cash"), lookback=300)

            if self.ksi_engine is None:
                try:
                    import ksi_engine
                    self.ksi_engine = ksi_engine.KSIEngine(4, 50) # 4 oscillators, 50 steps
                except Exception as e:
                    print(f"❌ Q-MATH :: Erro Crítico no Motor KSI: {e}")
                    self.ksi_engine = None

            if self.precog_node is None:
                self.precog_node = QuantumPreCognitionNode(symbol=getattr(self, "current_symbol", "GER40.cash"))

            current_close = df['close'].iloc[-1]
            
            # Funções helper para execução paralela (GIL Released in C++)
            def run_lbm(regime=0):
                lbm_signal = "LAMINAR_FLOW"
                lbm_v_current = None
                try:
                    # Passamos o slice_df completo para o novo motor v3.2
                    lbm_density, lbm_velocity = self.lbm_tracker.process_tick_stream(df.tail(150), steps=5)
                    if lbm_density is not None and lbm_velocity is not None:
                        lbm_signal = self.lbm_tracker.detect_squeeze_rupture(df.tail(150), lbm_density, lbm_velocity, current_regime=regime)
                        lbm_v_current = lbm_velocity
                except Exception as e:
                    print(f"[Q-Math] Erro LBM: {e}")
                return {"lbm_signal": lbm_signal, "lbm_v_current": lbm_v_current}

            def run_schrodinger():
                cloud_str = "0.0001:"
                prob_density = None
                sec_metrics = None
                try:
                    # V3.5: Evolução Temporal Ultra-Acelerada (dt=1.2, steps=15)
                    # v25.0: Acoplamento de Massa via PTI (Feedback Loop)
                    pti_val = getattr(self, "current_pti_context", 0.0)
                    density_schrod, _ = self.cloud_tracker.step(df.tail(200), dt=1.2, steps=15, pti=pti_val)
                    prob_density = density_schrod
                    sec_metrics = self.cloud_tracker.get_singularity_metrics()
                    if density_schrod is not None:
                        import numpy as np
                        cloud_str = f"{self.cloud_tracker.dx:.4f}:"
                        max_d = np.max(density_schrod)
                        cloud_arr = []
                        for i, d in enumerate(density_schrod):
                            if d > max_d * 0.10: 
                                p = self.cloud_tracker.index_to_price(i)
                                cloud_arr.append(f"{p:.2f}|{d:.4f}")
                        cloud_str += ",".join(cloud_arr)
                except Exception as e:
                    print(f"[Q-Math] Erro Schrödinger: {e}")
                return {"prob_density": prob_density, "sec_metrics": sec_metrics, "cloud_str": cloud_str}

            def run_plasma():
                z_pinch_signal = "NEUTRAL"
                try:
                    curr_candle = df.iloc[-1]; prev_candle = df.iloc[-2]
                    plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df.tail(200), lookback=200)
                    z_idx, z_type = self.plasma_tracker.process_tick(curr_candle, prev_candle, plasma_zones)
                    if z_idx > 1.0:
                        z_pinch_signal = f"Z_PINCH_PLASMA_{z_type}"
                except Exception as e:
                    pass
                return {"z_pinch_signal": z_pinch_signal}

            def run_rmt(lbm_v=None):
                rmt_signal = "NOISE"
                is_pure = False
                try:
                    # RMT v2.0: Agora recebe a velocidade do fluido para filtrar ruído cinético
                    _, power_ratio, is_pure = self.rmt_tracker.process_spectral_filter(df.tail(200), lbm_v)
                    rmt_signal = f"PURE_SIGNAL_x{power_ratio:.1f}" if is_pure else f"NOISE_x{power_ratio:.1f}"
                except Exception as e:
                    pass
                return {"rmt_signal": rmt_signal, "is_pure": is_pure}

            def run_qrw():
                qrw_signal = "NEUTRAL"
                qrw_history_str = ""
                try:
                    # 1. NORMALIZAÇÃO DE COLUNAS (Resiliência)
                    df.columns = [c.lower() for c in df.columns]
                    
                    # 2. ESCALA DINÂMICA COMPENSADA (v7.0)
                    recent_atr = (df['high'] - df['low']).tail(20).mean()
                    dynamic_scale = 1.0 / (recent_atr * 0.4 + 1e-9) if recent_atr > 0 else 0.01
                    
                    # 3. RECONSTRUÇÃO INCREMENTAL (State Persistence)
                    h_df = df.tail(800)
                    
                    if self.qrw_tracker.engine is None:
                        return {"qrw_signal": "OFFLINE", "qrw_history": ""}

                    if len(self.qrw_tracker.last_history) == 0 or len(df) < len(self.qrw_tracker.last_history):
                        self.qrw_tracker.engine.reset()
                        self.qrw_tracker.last_history = []
                        bars_to_process = h_df
                    else:
                        bars_to_process = df.tail(1) 
                    
                    # Prepara deltas e volumes
                    deltas = bars_to_process['close'].diff().fillna(0).values if len(bars_to_process) > 1 else (bars_to_process['close'] - bars_to_process['open']).values
                    volumes = bars_to_process['tick_volume'].values
                    
                    recent_atr = (df['high'] - df['low']).tail(7).mean()
                    scale = 50.0 / (recent_atr + 1e-9)
                    
                    # Injeção de Resiliência: Inicialização Zero-Point
                    curr_drift = 0.0
                    curr_entropy = 1.0

                    for i in range(len(bars_to_process)):
                        d = deltas[i]
                        v = volumes[i]
                        
                        # Evolução Quântica Única
                        self.qrw_tracker.engine.update_and_get_skew(
                            np.array([d], dtype=float),
                            np.array([v], dtype=float),
                            scale
                        )
                        
                        curr_drift = self.qrw_tracker.engine.get_skewness() 
                        curr_entropy = 1.0 # Entropy is now intrinsic to the wave collapse
                        
                        # Lógica de Sinal Impecável (v3.5)
                        # 1: BUY_SINGULARITY, 2: SELL_SINGULARITY, 3: BUY_FLOW, 4: SELL_FLOW
                        q_signal = 0
                        if abs(curr_drift) > 0.005 and curr_entropy > 1.0:
                            q_signal = 1 if curr_drift < 0 else 2 
                        elif abs(curr_drift) > 0.0001:
                            q_signal = 3 if curr_drift > 0 else 4
                        
                        # Armazena para persistência no HUD
                        self.qrw_tracker.last_history.append(q_signal)
                        if len(self.qrw_tracker.last_history) > 800:
                            self.qrw_tracker.last_history.pop(0)
                        
                    qrw_history_str = ",".join(map(str, self.qrw_tracker.last_history))
                    
                    # Sinal Atual com Telemetria Consolidada
                    curr_sig_code = self.qrw_tracker.last_history[-1] if self.qrw_tracker.last_history else 0
                    diag_info = f"D:{curr_drift:+.3f} H:{curr_entropy:.2f}"
                    
                    if curr_sig_code == 2: qrw_signal = "QUANTUM_EXHAUSTION_SHORT"
                    elif curr_sig_code == 1: qrw_signal = "QUANTUM_EXHAUSTION_LONG"
                    elif curr_sig_code == 3: qrw_signal = "QUANTUM_ACCUMULATION_BULL"
                    elif curr_sig_code == 4: qrw_signal = "QUANTUM_DISTRIBUTION_BEAR"
                    # QRW Resilience complete.
                        
                except Exception as e:
                    qrw_signal = f"ERR: {type(e).__name__}"
                return {"qrw_signal": qrw_signal, "qrw_history": qrw_history_str}

            def run_qcd():
                qcd_signal = "CONFINED"
                try:
                    qcd_signal = self.qcd_tracker.detect_fission(df)
                except Exception as e:
                    print(f"[Q-Math] Erro Market QCD: {e}")
                return {"qcd_signal": qcd_signal}

            def run_rht():
                rht_status = "PURIFYING"
                rht_history = ""
                rht_flash = 0.0
                rht_flash_history = ""
                try:
                    # O RHT v2.0 processa tensores multi-TF em escala termodinâmica
                    rht_status, history_arr, rht_flash, rht_flash_history = self.rht_tracker.process_live_rht()
                    rht_history = ",".join(history_arr)
                except Exception as e:
                    print(f"[Q-Math] Erro RHT: {e}")
                return {"rht_status": rht_status, "rht_history": rht_history, "rht_flash": rht_flash, "rht_flash_history": rht_flash_history}

            def run_cyt():
                ricci_curvature = 0.0
                cyt_danger = 0.0
                try:
                    import numpy as np
                    # V3.6: Reduzido lookback para 34 barras para detecção ultra-sensível de reversão
                    recent_df = df.tail(34).copy()
                    N = len(recent_df)
                    data_10d = np.zeros((10, N))
                    data_10d[0, :] = recent_df['open'].values
                    data_10d[1, :] = recent_df['high'].values
                    data_10d[2, :] = recent_df['low'].values
                    data_10d[3, :] = recent_df['close'].values
                    data_10d[4, :] = recent_df['tick_volume'].values
                    data_10d[5, :] = recent_df['close'].pct_change().bfill().values
                    data_10d[6, :] = (recent_df['high'] - recent_df['low']).values
                    data_10d[7, :] = recent_df['close'].rolling(5).mean().bfill().values
                    data_10d[8, :] = recent_df['tick_volume'].rolling(5).mean().bfill().values
                    data_10d[9, :] = (recent_df['close'] - recent_df['open']).values
                    
                    flow = self.cyt.analyze_manifold_flow(data_10d)
                    def_array = flow["deformation"]
                    det_array = flow["determinant"]
                    danger_array = self.cyt.calculate_danger_zones(data_10d, 15, 2.5) # Reduzido window para 15
                    
                    if len(def_array) > 0:
                        ricci_curvature = def_array[-1]
                        cyt_danger = danger_array[-1]
                        
                        # Calculo de Entropia Holográfica (AdS/CFT)
                        # Usamos o determinante métrico e o volume de tick local
                        local_vol = np.sum(data_10d[4, -10:])
                        local_spread = np.mean(data_10d[6, -10:])
                        h_entropy = self.cyt.calculate_holographic_entropy(local_vol, 10.0, local_spread)
                        
                        # Detecção de Colapso de Variedade
                        collapse_info = self.cyt.calculate_topological_collapse(data_10d)
                        is_collapsed = collapse_info["is_collapsed"]
                except Exception as e:
                    print(f"[Q-Math] Erro CYT Ricci Flow: {e}")
                    h_entropy = 0.0
                    is_collapsed = False
                return {"ricci_curvature": ricci_curvature, "cyt_danger": cyt_danger, "h_entropy": h_entropy, "is_collapsed": is_collapsed}

            def run_ksi():
                ksi_val = 0.0
                if self.ksi_engine is not None and len(df) >= 100:
                    try:
                        import numpy as np
                        recent_df = df.tail(100).copy()
                        N = 50
                        data_4d = np.zeros((4, N))
                        data_4d[0, :] = recent_df['close'].rolling(3).mean().tail(N).values
                        data_4d[1, :] = recent_df['close'].rolling(8).mean().tail(N).values
                        data_4d[2, :] = recent_df['close'].rolling(14).mean().tail(N).values
                        data_4d[3, :] = recent_df['close'].rolling(21).mean().tail(N).values
                        
                        self.ksi_engine.load_oscillator_data(data_4d)
                        self.ksi_engine.compute_synchronization()
                        ksi_val = self.ksi_engine.get_current_ksi()
                    except Exception as e:
                        pass
                return {"ksi_val": ksi_val}

            def run_precog():
                # Calcula ATR
                atr = df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min()
                if atr == 0: atr = 10.0
                try:
                    res = self.precog_node.project_containment_horizon(df, current_close, atr)
                    return {"precog_sl_long": res.get("sl_bull_singular", 0.0), 
                            "precog_sl_short": res.get("sl_bear_singular", 0.0)}
                except Exception:
                    return {"precog_sl_long": current_close - (atr*3), "precog_sl_short": current_close + (atr*3)}

            # Orquestração Paralela de Física (LBM primeiro para prover velocidade ao RMT)
            lbm_res = run_lbm(regime=getattr(self, "current_regime_context", 0))
            lbm_v = lbm_res.get("lbm_v_current")

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = [
                    executor.submit(run_schrodinger),
                    executor.submit(run_plasma),
                    executor.submit(run_rmt, lbm_v),
                    executor.submit(run_qrw),
                    executor.submit(run_qcd),
                    executor.submit(run_rht),
                    executor.submit(run_cyt),
                    executor.submit(run_ksi),
                    executor.submit(run_precog)
                ]
                
                results = {"lbm_signal": lbm_res["lbm_signal"]}
                for future in concurrent.futures.as_completed(futures):
                    results.update(future.result())

            # Atualização atômica do estado que será lido pelo AGI_CORE
            with self.state_lock:
                self.current_state["status"] = "ACTIVE"
                self.current_state["latest_price"] = current_close
                self.current_state["cloud_prob"] = results.get("prob_density", [])
                self.current_state["sec_metrics"] = results.get("sec_metrics")
                self.current_state["cloud_str"] = results.get("cloud_str", "0.0001:")
                self.current_state["lbm_signal"] = results.get("lbm_signal", "LAMINAR_FLOW")
                self.current_state["z_pinch_signal"] = results.get("z_pinch_signal", "NEUTRAL")
                self.current_state["rmt_signal"] = results.get("rmt_signal", "NOISE")
                self.current_state["qrw_signal"] = results.get("qrw_signal", "NEUTRAL")
                self.current_state["qrw_history"] = results.get("qrw_history", "")
                self.current_state["is_pure"] = results.get("is_pure", False)
                self.current_state["qcd_signal"] = results.get("qcd_signal", "CONFINED")
                self.current_state["rht_status"] = results.get("rht_status", "PURIFYING")
                self.current_state["rht_history"] = results.get("rht_history", "")
                self.current_state["rht_flash"] = results.get("rht_flash", 0.0)
                self.current_state["rht_flash_history"] = results.get("rht_flash_history", "")
                self.current_state["ricci_curvature"] = results.get("ricci_curvature", 0.0)
                self.current_state["cyt_danger"] = results.get("cyt_danger", 0.0)
                self.current_state["h_entropy"] = results.get("h_entropy", 0.0)
                self.current_state["is_collapsed"] = results.get("is_collapsed", False)
                self.current_state["ksi_val"] = results.get("ksi_val", 0.0)
                self.current_state["precog_sl_long"] = results.get("precog_sl_long", current_close)
                self.current_state["precog_sl_short"] = results.get("precog_sl_short", current_close)

        except Exception as e:
            print(f"❌ Q-MATH :: Erro no processamento interno: {e}")

    def run_subscriber_loop(self):
        """Thread que escuta o mercado em loop"""
        print("⚛️ Q-MATH :: Assinante de Mercado (SUB) Iniciado.")
        while self.is_running:
            latest_payload = None
            while True:
                try:
                    msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                    topic = msg[0].decode('utf-8')
                    if topic == TOPIC_MARKET_BAR:
                        latest_payload = pickle.loads(msg[1])
                except zmq.Again:
                    break
                except Exception as e:
                    print(f"❌ Q-MATH :: Erro de rede SUB: {e}")
                    break

            if latest_payload is not None:
                self.process_market_data(latest_payload)
            else:
                time.sleep(0.01) # Sleep minúsculo para não queimar CPU enquanto espera

    def run_reply_server(self):
        """Thread principal que atende os pedidos de estado do AGI_CORE"""
        print(f"⚛️ Q-MATH :: Servidor de Respostas (REP) Iniciado na porta {PORT_Q_MATH}.")
        while self.is_running:
            try:
                # Aguarda pedido do AGI CORE (pode conter o regime atual e PTI para feedback)
                message = self.rep_socket.recv()
                
                # Protocolo: "GET_STATE|r_score|pti"
                try:
                    msg_str = message.decode('utf-8')
                    parts = msg_str.split("|")
                    if len(parts) >= 2:
                        self.current_regime_context = int(parts[1])
                    if len(parts) >= 3:
                        self.current_pti_context = float(parts[2])
                    else:
                        self.current_pti_context = 0.0
                except:
                    self.current_regime_context = 0
                    self.current_pti_context = 0.0
                
                with self.state_lock:
                    # Empacota o estado atual e envia de volta imediatamente
                    reply = pickle.dumps(self.current_state)
                
                self.rep_socket.send(reply)
            except Exception as e:
                print(f"❌ Q-MATH :: Erro no REP Server: {e}")
                time.sleep(0.1)

    def startup(self):
        self.is_running = True
        
        # [PROTOCOL NEXUS] Inicialização mandatória para trackers que consultam o terminal diretamente (RHT)
        if not mt5.initialize():
            print("❌ Q-MATH :: Falha ao inicializar API MT5. RHT operará em modo degradado.")
        else:
            print("⚛️ Q-MATH :: API MT5 Sincronizada para trackers multi-fractais.")

        # Inicia a Thread SUB (Ouvinte)
        threading.Thread(target=self.run_subscriber_loop, daemon=True).start()
        
        # O REP server roda na thread principal
        self.run_reply_server()

    def shutdown(self):
        self.is_running = False
        self.sub_socket.close()
        self.rep_socket.close()
        self.sub_context.term()
        self.rep_context.term()
        mt5.shutdown()
        print("⚛️ Q-MATH :: Desligado.")

if __name__ == "__main__":
    node = QMathNode()
    try:
        node.startup()
    except KeyboardInterrupt:
        node.shutdown()
