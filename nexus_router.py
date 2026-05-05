"""
NEXUS ROUTER (ZMQ PUB Node)
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
from Code.R_Exec.mt5_bridge import MT5NeuralBridge
from Code.N_Core.swarm_bus import create_publisher, create_subscriber, PORT_TICK_FEED, PORT_CONTROL, TOPIC_MARKET_BAR, TOPIC_CONTROL

class NexusRouter:
    def __init__(self, symbol="GER40.cash", timeframe=mt5.TIMEFRAME_H2):
        self.symbol = symbol
        self.timeframe = timeframe
        self.bridge = MT5NeuralBridge(self.symbol)
        
        self.pub_context, self.pub_socket = create_publisher(PORT_TICK_FEED)
        self.sub_context, self.sub_socket = create_subscriber(PORT_CONTROL, TOPIC_CONTROL)
        
        self.is_running = False

    def startup(self):
        print(f"📡 NEXUS ROUTER :: Iniciando Roteamento PUB/SUB para {self.symbol}...")
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
                        if new_tf != self.timeframe:
                            self.timeframe = new_tf
                            print(f"\n📡 NEXUS ROUTER :: Timeframe alterado para: {self.timeframe}. Limpando feed...")
                            time.sleep(0.5)
                except zmq.Again:
                    pass

                # Extrai barras
                rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 1000)
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    
                    # Cria o pacote de dados com o timeframe novo embutido
                    payload = {
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "timestamp": time.time(),
                        "data": df
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

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus Router - ZMQ PUB")
    parser.add_argument('--symbol', type=str, default="GER40.cash", help='Symbol to trade')
    args = parser.parse_args()
    
    router = NexusRouter(symbol=args.symbol)
    if router.startup():
        try:
            router.run_broadcast_loop()
        except KeyboardInterrupt:
            router.shutdown()
