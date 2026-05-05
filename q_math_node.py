"""
Q-MATH NODE (ZMQ SUB / REP Node)
Função: Assina (SUB) os dados de mercado do NEXUS ROUTER.
Atualiza em background todos os trackers pesados de C++ (LBM, Schrödinger, RMT).
Levanta um servidor (REP) para que o AGI_CORE consulte os dados calculados instantaneamente.
"""
import time
import threading
import MetaTrader5 as mt5
import pickle
import sys
import zmq

from Code.N_Core.swarm_bus import create_subscriber, create_reply_server, PORT_TICK_FEED, PORT_Q_MATH, TOPIC_MARKET_BAR

# Trackers C++ / Física Pesada
from Code.N_Core.quantum_clouds import QuantumCloudTracker
from Code.N_Core.fluid_dynamics import LBMFluidDynamics
from Code.N_Core.plasma_market import PlasmaMarketTracker
from Code.N_Core.random_matrix import RandomMatrixTracker
from Code.N_Core.quantum_walk import QRWTracker

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
        
        # Estado atual cacheado para responder rapidamente
        self.current_state = {
            "status": "INITIALIZING",
            "lbm_zones": [],
            "cloud_zones": [],
            "rmt_signal": 0.0,
            "qrw_density": []
        }
        
        # Trava para evitar conflito de leitura/escrita no estado interno
        self.state_lock = threading.Lock()

    def process_market_data(self, df, tf=None):
        """Processa a barra recebida e atualiza os motores C++"""
        try:
            # Se mudou o timeframe, destroi a física antiga para resetar
            if tf is not None and getattr(self, "active_tf", None) != tf:
                print(f"\n⚛️ Q-MATH :: Salto Dimensional Detectado. Recriando física para TF: {tf}")
                self.active_tf = tf
                self.cloud_tracker = None
                self.lbm_tracker = None
                self.plasma_tracker = None
                self.rmt_tracker = None
                self.qrw_tracker = None

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
                self.qrw_tracker = QRWTracker(positions=201)

            # Atualização dos Trackers Pesados
            current_close = df['close'].iloc[-1]
            
            # 1. LBM Step
            lbm_signal = "LAMINAR_FLOW"
            try:
                lbm_density, lbm_velocity = self.lbm_tracker.process_tick_stream(df.tail(10), steps=5)
                if lbm_density is not None and lbm_velocity is not None:
                    lbm_signal = self.lbm_tracker.detect_squeeze_rupture(current_close, lbm_density, lbm_velocity)
            except Exception as e:
                print(f"[Q-Math] Erro LBM: {e}")

            # 2. Schrödinger Step
            cloud_str = "0.0001:"
            prob_density = None
            sec_metrics = None
            try:
                # Usa 200 barras como o monólito fazia para dar massa à nuvem
                density_schrod, _ = self.cloud_tracker.step(df.tail(200), dt=0.2, steps=5)
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

            # 3. Plasma / Z-Pinch Step
            z_pinch_signal = "NEUTRAL"
            try:
                curr_candle = df.iloc[-1]; prev_candle = df.iloc[-2]
                plasma_zones = self.plasma_tracker.scan_for_plasma_zones(df.tail(200), lookback=200)
                z_idx, z_type = self.plasma_tracker.process_tick(curr_candle, prev_candle, plasma_zones)
                if z_idx > 90.0:
                    z_pinch_signal = f"Z_PINCH_{z_type}"
            except Exception as e:
                pass

            # 4. RMT Step
            rmt_signal = "NOISE"
            try:
                _, power_ratio, is_pure = self.rmt_tracker.process_spectral_filter(df.tail(200))
                if is_pure: rmt_signal = f"PURE_SIGNAL_x{power_ratio:.1f}"
            except Exception as e:
                pass

            # 5. QRW Step
            qrw_signal = "NEUTRAL"
            try:
                if self.qrw_tracker.is_in_range(df, lookback=20):
                    _, qrw_signal = self.qrw_tracker.process_qrw_skewness(df, lookback=20)
            except Exception as e:
                pass

            # Atualização atômica do estado que será lido pelo AGI_CORE
            with self.state_lock:
                self.current_state["status"] = "ACTIVE"
                self.current_state["latest_price"] = current_close
                self.current_state["cloud_prob"] = prob_density if prob_density is not None else []
                self.current_state["sec_metrics"] = sec_metrics
                self.current_state["cloud_str"] = cloud_str
                self.current_state["lbm_signal"] = lbm_signal
                self.current_state["z_pinch_signal"] = z_pinch_signal
                self.current_state["rmt_signal"] = rmt_signal
                self.current_state["qrw_signal"] = qrw_signal
                self.current_state["is_pure"] = is_pure if 'is_pure' in locals() else False

        except Exception as e:
            print(f"❌ Q-MATH :: Erro no processamento interno: {e}")

    def run_subscriber_loop(self):
        """Thread que escuta o mercado em loop"""
        print("⚛️ Q-MATH :: Assinante de Mercado (SUB) Iniciado.")
        while self.is_running:
            latest_df = None
            latest_tf = None
            while True:
                try:
                    msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                    topic = msg[0].decode('utf-8')
                    if topic == TOPIC_MARKET_BAR:
                        payload = pickle.loads(msg[1])
                        latest_df = payload.get("data")
                        latest_tf = payload.get("timeframe")
                except zmq.Again:
                    break
                except Exception as e:
                    print(f"❌ Q-MATH :: Erro de rede SUB: {e}")
                    break

            if latest_df is not None:
                self.process_market_data(latest_df, latest_tf)
            else:
                time.sleep(0.01) # Sleep minúsculo para não queimar CPU enquanto espera

    def run_reply_server(self):
        """Thread principal que atende os pedidos de estado do AGI_CORE"""
        print(f"⚛️ Q-MATH :: Servidor de Respostas (REP) Iniciado na porta {PORT_Q_MATH}.")
        while self.is_running:
            try:
                # Aguarda pedido do AGI CORE
                message = self.rep_socket.recv()
                
                with self.state_lock:
                    # Empacota o estado atual e envia de volta imediatamente
                    reply = pickle.dumps(self.current_state)
                
                self.rep_socket.send(reply)
            except Exception as e:
                print(f"❌ Q-MATH :: Erro no REP Server: {e}")
                time.sleep(0.1)

    def startup(self):
        self.is_running = True
        # Inicia a Thread SUB (Ouvinte)
        threading.Thread(target=self.run_subscriber_loop, daemon=True).start()
        
        # O REP server roda na thread principal
        self.run_reply_server()

if __name__ == "__main__":
    node = QMathNode()
    try:
        node.startup()
    except KeyboardInterrupt:
        node.is_running = False
        node.sub_socket.close()
        node.rep_socket.close()
        node.sub_context.term()
        node.rep_context.term()
        print("⚛️ Q-MATH :: Desligado.")
