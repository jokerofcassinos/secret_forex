"""
SWARM BUS: Ponto central de comunicação do Actor System via ZeroMQ.
Define as portas, endereços e tópicos de Pub/Sub para a AGI Corporativa.
"""
import zmq
import json
import pickle

# Endereços e Portas Padrão
HOST = "tcp://127.0.0.1"
PORT_TICK_FEED = "5555" # Porta PUB/SUB para dados do MT5 (Nexus Router)
PORT_Q_MATH = "5556"    # Porta REQ/REP para cálculos quânticos pesados (Q-Math Node)
PORT_LOGS = "5557"      # Porta PUB/SUB para envio de logs corporativos
PORT_CONTROL = "5558"   # Porta PUB/SUB para controle de Swarm (Timeframe, Reset)

# Tópicos do Roteador (PUB/SUB)
TOPIC_MARKET_TICK = "MKT_TICK"
TOPIC_MARKET_BAR = "MKT_BAR"
TOPIC_CONTROL = "CTRL"

def create_publisher(port):
    """Cria um socket ZMQ Publisher"""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.bind(f"{HOST}:{port}")
    return context, socket

def create_subscriber(port, topic=""):
    """Cria um socket ZMQ Subscriber"""
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(f"{HOST}:{port}")
    socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    return context, socket

def create_reply_server(port):
    """Cria um socket ZMQ Reply (Servidor RPC)"""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.LINGER, 0)
    socket.bind(f"{HOST}:{port}")
    return context, socket

def create_request_client(port):
    """Cria um socket ZMQ Request (Cliente RPC)"""
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(f"{HOST}:{port}")
    return context, socket

def send_data(socket, topic, data, use_pickle=True):
    """Envia dados via ZMQ, serializando com Pickle ou JSON"""
    payload = pickle.dumps(data) if use_pickle else json.dumps(data).encode('utf-8')
    socket.send_multipart([topic.encode('utf-8'), payload])

def receive_data(socket, use_pickle=True):
    """Recebe e desserializa dados via ZMQ"""
    msg = socket.recv_multipart()
    topic = msg[0].decode('utf-8')
    payload = msg[1]
    data = pickle.loads(payload) if use_pickle else json.loads(payload.decode('utf-8'))
    return topic, data
