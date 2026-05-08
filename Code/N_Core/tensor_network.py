import numpy as np
import pandas as pd
import sys
import os

# Configuração de caminhos para encontrar as DLLs
current_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(os.path.dirname(current_dir))

if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)

sys.path.append(root_path)

import qdd_engine

class TensorNetworkNode:
    """
    NEXUS QDD - TENSOR NETWORK ORCHESTRATOR
    Sincroniza múltiplos timeframes e calcula o alinhamento dimensional global.
    """
    def __init__(self):
        # dim=1, hbar=1.0, gamma=0.05
        self.engine = qdd_engine.QDDEngine(1, 1.0, 0.05)
        self.lookback = 128 # Janela de observação para contração
        
    def calculate_global_alignment(self, tf_data_dict):
        """
        Recebe um dicionário { 'M1': df, 'M5': df, 'M15': df, 'H1': df }
        Retorna a Fidelidade Global (-1.0 a 1.0)
        """
        if not tf_data_dict or len(tf_data_dict) < 2:
            return 0.0

        # Prepara a matriz para o C++ [num_tfs][lookback]
        # Precisamos garantir que todos os arrays tenham o mesmo tamanho
        matrix_data = []
        
        for tf, df in tf_data_dict.items():
            if len(df) < self.lookback:
                # Padding com o primeiro valor se for muito curto
                prices = df['close'].values.astype(np.float64)
                pad_width = self.lookback - len(prices)
                prices = np.pad(prices, (pad_width, 0), 'edge')
            else:
                prices = df['close'].tail(self.lookback).values.astype(np.float64)
            
            matrix_data.append(prices)
        
        multi_tf_matrix = np.array(matrix_data)
        
        # Chama a contração tensorial no C++
        # Cutoff_level=2 (Filtro de ruído moderado)
        global_fidelity = self.engine.calculate_global_fidelity(multi_tf_matrix, cutoff_level=2)
        
        return global_fidelity

    def get_alignment_status(self, fidelity):
        """Traduz a fidelidade em estados legíveis pelo Swarm"""
        if fidelity > 0.8:
            return "QUANTUM_ENTANGLEMENT_BULL"
        elif fidelity < -0.8:
            return "QUANTUM_ENTANGLEMENT_BEAR"
        elif abs(fidelity) < 0.2:
            return "DIMENSIONAL_DECOHERENCE (NOISE)"
        else:
            return "SUPERPOSITION_STATE"

if __name__ == "__main__":
    print("NEXUS TENSOR NETWORK: Sistema de Alinhamento Dimensional Pronto.")
