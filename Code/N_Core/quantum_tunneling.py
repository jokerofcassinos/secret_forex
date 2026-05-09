import os
import sys
import numpy as np
import pandas as pd

# Configuração de Caminhos para DLLs
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

try:
    import qte_engine
except ImportError:
    print("FAIL: qte_engine não encontrado. Certifique-se de compilar primeiro.")

class QuantumTunnelingNode:
    """
    Orquestrador do Efeito de Tunelamento para Take Profit.
    Analisa a barreira de liquidez (Potential Barrier) e decide se o preço
    tem energia suficiente para atravessar ou se deve realizar lucro.
    """
    def __init__(self):
        self.engine = qte_engine.QTEEngine()
        self.lookback = 100
        
    def calculate_exit_probability(self, df, current_price, cloud_density):
        """
        cloud_density: array de densidade da nuvem de Schrodinger no entorno do preço.
        Retorna a probabilidade de TUNELAMENTO.
        Se > 0.8: MANTÉM (O preço vai atravessar a resistência).
        Se < 0.2: TP (O preço vai ricochetear).
        """
        # Estima a Energia Cinética (E) baseada na volatilidade e momentum
        returns = df['close'].pct_change().tail(20)
        volatility = returns.std()
        momentum = (df['close'].iloc[-1] / df['close'].iloc[-20]) - 1.0
        
        # Energia E = Escala de Momentum corrigida pela volatilidade
        energy_e = abs(momentum) / (volatility + 1e-9)
        
        # Normaliza a barreira (V)
        # cloud_density vem do Q-Math como um vetor puro de densidades
        v_barrier = np.array(cloud_density)
        
        # Cálculo C++
        t_prob = self.engine.calculate_tunneling_probability(current_price, energy_e, v_barrier)
        
        return t_prob

    def get_tp_advice(self, t_prob):
        if t_prob <= 0:
            return "SCANNING_BARRIER"
        if t_prob > 0.85:
            return "HOLD_FOR_TUNNELING"
        elif t_prob < 0.15:
            return "QUANTUM_EXIT_NOW"
        else:
            return "STABLE_ORBIT"

if __name__ == "__main__":
    # Teste de Sanidade
    node = QuantumTunnelingNode()
    fake_barrier = np.random.exponential(1.0, 50)
    prob = node.engine.calculate_tunneling_probability(100.0, 0.5, fake_barrier)
    print(f"DEBUG: Probabilidade de Tunelamento (Simulada): {prob:.4f}")
