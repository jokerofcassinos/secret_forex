"""
NEXUS ROUTER (ZMQ PUB Node - v2.1)

Função: Extrair dados de mercado (Ticks/Bars) da API MT5 o mais rápido possível
e realizar o Broadcast via rede ZeroMQ para o Swarm.
Não possui lógica analítica pesada. Apenas Ingestão e Roteamento de Dados.
"""
import time
import MetaTrader5 as mt5
import pandas as pd
import zmq
import pickle
import argparse
import sys
import os


# [BOOTLOADER] Força reconhecimento dos binários Mingw64
if os.name == 'nt' and os.path.exists(r"D:\msys64\mingw64\bin"):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")


from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.swarm_bus import create_publisher, create_subscriber, PORT_TICK_FEED, PORT_CONTROL, TOPIC_MARKET_BAR, TOPIC_CONTROL

class NexusRouter:
    def __init__(self, symbol=None, timeframe=None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.bridge = MT5NeuralBridge(self.symbol)
        
        self.pub_context, self.pub_socket = create_publisher(PORT_TICK_FEED)
        self.sub_context, self.sub_socket = create_subscriber(PORT_CONTROL, TOPIC_CONTROL)
        
        self.is_running = False

    def startup(self):
        print(f"📡 NEXUS ROUTER :: Iniciando Roteamento PUB/SUB...")
        
        # Se não há símbolo (Modo Agnóstico), inicializamos apenas o básico
        if self.symbol is None:
            print("📡 NEXUS ROUTER :: Modo Agnóstico. Aguardando sinal do MT5 para sintonizar...")
            # Precisamos inicializar o MT5 mesmo sem símbolo para poder receber mensagens depois
            if not mt5.initialize():
                print("❌ NEXUS ROUTER :: Falha ao inicializar MT5.")
                return False
            self.is_running = True
            return True

        if not self.bridge.initialize():
            print("❌ NEXUS ROUTER :: Falha ao conectar ao MT5.")
            return False
        # Faz um aquecimento do buffer interno do bridge
        self.bridge.fetch_full_history(count=5000)
        self.is_running = True
        return True

    def run_broadcast_loop(self):
        print(f"📡 NEXUS ROUTER :: Transmissão AO VIVO na porta {PORT_TICK_FEED} [ON]")
        
        while self.is_running:
            try:
                # Checa por mensagens de controle de Timeframe
                try:
                    msg = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)
                    topic = msg[0].decode('utf-8')
                    payload = pickle.loads(msg[1])
                    if payload.get("action") == "CHANGE_TF":
                        new_tf = payload.get("timeframe")
                        new_sym = payload.get("symbol")
                        
                        # Sincronização de Símbolo (Singularidade)
                        if new_sym and new_sym != self.symbol:
                            self.symbol = new_sym
                            self.bridge.symbol = new_sym
                            self.bridge.initialize() # Força seleção no Market Watch
                            self.bridge.fetch_full_history(count=1000) # Força o MT5 a baixar os dados para a RAM
                            print(f"\n📡 NEXUS ROUTER :: Ativo sintonizado: {self.symbol}")
                            
                        # Sincronização de Timeframe
                        if new_tf != self.timeframe:
                            self.timeframe = new_tf
                            print(f"📡 NEXUS ROUTER :: Timeframe alterado para: {self.timeframe}. Limpando feed...")
                            time.sleep(0.5)
                except zmq.Again:
                    pass

                # Se a realidade ainda não colapsou (sem símbolo/tf), aguarda
                if self.symbol is None or self.timeframe is None:
                    time.sleep(1)
                    continue

                # Extrai barras do TF principal e das Âncoras Dimensionais (Quadri-Dimensional TQFM)
                payload_data = {}
                
                # 0. Focus TF (O gráfico atual do usuário - para renderização holográfica)
                # print(f"DEBUG: Fetching Focus TF {self.timeframe}")
                rates_focus = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 1000)
                if rates_focus is not None and len(rates_focus) > 0:
                    payload_data['focus'] = pd.DataFrame(rates_focus)
                else:
                    print(f"⚠️ NEXUS ROUTER :: Falha ao extrair Focus TF ({self.timeframe}) para {self.symbol}. Terminal ocupado ou sem dados.")
                    
                # 1. Espectro DEEP MACRO (D1) - Curvatura do Universo e Gravidade Secular
                # print("DEBUG: Fetching D1")
                rates_d1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_D1, 0, 500)
                if rates_d1 is not None and len(rates_d1) > 0:
                    payload_data['d1'] = pd.DataFrame(rates_d1)
                    
                # 2. Espectro MACRO ESTRUTURAL (H4) - Memória de Longo Prazo e Marés
                # print("DEBUG: Fetching H4")
                rates_h4 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H4, 0, 800)
                if rates_h4 is not None and len(rates_h4) > 0:
                    payload_data['h4'] = pd.DataFrame(rates_h4)
                    
                # 3. Espectro MESO / TOPOLÓGICO (M15) - Alinhamento e Direção Tática
                # print("DEBUG: Fetching M15")
                rates_m15 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 1000)
                if rates_m15 is not None and len(rates_m15) > 0:
                    payload_data['m15'] = pd.DataFrame(rates_m15)
                    
                # 4. Espectro MICRO / CINÉTICO (M1) - Gatilho, Turbulência e Execução HFT
                # print("DEBUG: Fetching M1")
                rates_m1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 1000)
                if rates_m1 is not None and len(rates_m1) > 0:
                    payload_data['m1'] = pd.DataFrame(rates_m1)

                if 'focus' in payload_data:
                    # Cria o pacote de dados estendido
                    payload = {
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "timestamp": time.time(),
                        "data": payload_data['focus'],  # Retrocompatibilidade
                        "data_mtf": payload_data       # Arquitetura Quadri-Dimensional TQFM
                    }
                    
                    serialized = pickle.dumps(payload)
                    self.pub_socket.send_multipart([TOPIC_MARKET_BAR.encode('utf-8'), serialized])
                    
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ NEXUS ROUTER :: Erro de Broadcast: {e}")
                time.sleep(1)
                
    def shutdown(self):
        self.is_running = False
        self.pub_socket.close()
        self.sub_socket.close()
        self.pub_context.term()
        self.sub_context.term()
        mt5.shutdown()
        print("📡 NEXUS ROUTER :: Desligado.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=str, default=None, help='Symbol to trade (None = wait for control)')
    args = parser.parse_args()
    
    router = NexusRouter(symbol=args.asset)

    if router.startup():
        try:
            router.run_broadcast_loop()
        except KeyboardInterrupt:
            router.shutdown()
