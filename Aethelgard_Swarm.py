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
            r_score, conf = self.q_logic.advanced_regime_score(slice_df, self.prev_s, self.prev_c)
            
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
            self.sec_cache.append("0|0|0")
            if len(self.sec_cache) > 300: self.sec_cache.pop(0)

            scores_hist.append(r_score)
            self.prev_s, self.prev_c = r_score, conf
        
        self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df, scores_hist)]
        self.last_time = df.iloc[-1]['time']
        self.rht_cache = ["0"] * 300
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] Boot N-Core Concluído.")

    def live_evolution_loop(self):
        global nexus_data_str, current_mt5_tf
        print("🧠 SWARM CORE :: Loop Evolutivo Iniciado. Aguardando Nexus Router...")
        
        try:
            while self.is_running:
                # Checa se o MT5 pediu uma mudança de Timeframe
                if current_mt5_tf is not None and self.active_tf != current_mt5_tf:
                    self.active_tf = current_mt5_tf
                    print(f"\n🌀 SWARM CORE :: Detectada Mudança Dimensional (TF: {self.active_tf}). Realinhando Redes...")
                    
                    # 1. Limpa os caches neurais para forçar recalculo no Python
                    self.regimes_cache.clear()
                    self.sec_cache.clear()
                    self.dots_cache.clear()
                    self.last_time = 0
                    
                    # 2. Informa o Router e o Q-Math para mudarem a janela
                    ctrl_payload = pickle.dumps({"action": "CHANGE_TF", "timeframe": self.active_tf})
                    self.ctrl_socket.send_multipart([TOPIC_CONTROL.encode('utf-8'), ctrl_payload])
                    time.sleep(0.5) # Dá um respiro para os nodos reiniciarem

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

                        if r_score == 1:
                            status_txt = "BULL_PREVISAO" if not self.is_sovereign else "TSUNAMI_BULL_ATIVO"
                        elif r_score == 2:
                            status_txt = "BEAR_PREVISAO" if not self.is_sovereign else "TSUNAMI_BEAR_ATIVO"
                        else:
                            status_txt = "AGUARDANDO_IGNICAO"

                        is_genesis = (self.prev_s != r_score)
                        if is_genesis: self.genesis_count = 0
                        self.is_sovereign = True 

                        sec_state = 1 if len(q_state.get("cloud_prob", [])) > 0 else 0
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
                            self.sec_cache.append("0|0|0")
                            if len(self.sec_cache) > 300: self.sec_cache.pop(0)

                            scores_list = [int(r.split('|')[0]) for r in self.regimes_cache]
                            self.dots_cache = [str(d) for d in self.q_logic.calculate_tactical_dots(df.tail(len(self.regimes_cache)), scores_list)]
                            
                            self.prev_s, self.prev_c = r_score, conf
                            self.last_time = df.iloc[-1]['time']

                        rt_regime = f"{r_score if self.is_sovereign else 0}|{conf}"
                        display_regimes = self.regimes_cache[1:] + [rt_regime]
                        
                        # Extrai a telemetria quântica do nó Q-MATH
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
                        
                        sec_str = "0|0|0"
                        if sec_m:
                            is_coll = (sec_m.get('singularity_strength', 0) > 0.04)
                            sec_state = 1 if is_coll else 0
                            rounded_peak = round(sec_m.get('peak_price', current_close) * 2) / 2
                            sec_str = f"{sec_state}|{rounded_peak:.2f}|{(sec_m.get('schwarzschild_radius', 0)):.2f}"
                            if is_coll and len(self.sec_cache) > 0:
                                self.sec_cache[-1] = sec_str
                        else:
                            sec_str = f"{sec_state}|{current_close:.2f}|0.00"

                        cyt_danger_cache = ["0"] * len(self.regimes_cache) # Pode ser implementado no yield_governor depois
                        rht_status_local = "PURIFYING"
                        
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal};{qrw_signal};{','.join(self.lbm_cache)};{','.join(self.z_pinch_cache)};{','.join(self.qrw_cache)};{','.join(cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_status_local};{','.join(self.rht_cache)}"
                        
                        sys.stdout.write(f"\r🧠 SWARM CORE :: Processado {current_close:.2f} | R: {r_score} | SEC: {sec_state}      ")
                        sys.stdout.flush()
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
