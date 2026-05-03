import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Resolve problema de DLL do MinGW no Windows para Python 3.8+
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

# Importa o módulo C++ compilado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../CPP_Engine")))
try:
    import cyt_engine.cp313_win_amd64 as cyt_engine_module
except ImportError:
    try:
        import cyt_engine as cyt_engine_module
    except ImportError as e:
        raise RuntimeError(f"FALHA CRÍTICA: Motor CYT (C++) não encontrado. {e}")

class YieldGovernor:
    """
    Agente Yield-Governor v1.2: Soberania Topológica H2.
    Especialista em detecção de colapsos invisíveis e proteção de capital.
    """
    def __init__(self, shield_threshold=2.5):
        self.engine = cyt_engine_module.CYTEngine()
        self.shield_threshold = shield_threshold
        self.history_deformation = []
        self.shield_active = False
        self.shield_level = 0.0

    def monitor_topology(self, data_10d: np.ndarray):
        if data_10d.shape[0] != 10:
            raise ValueError("Matriz de entrada deve possuir 10 dimensões.")

        # 1. Processamento C++ (Ricci Flow Proxy)
        deformations = self.engine.calculate_deformation(data_10d)
        
        # 2. Avaliação de Escudo Adaptativa
        # Usamos uma janela curta para o escudo reagir ao clímax do warm-up
        self.shield_level = self.engine.calculate_neutron_shield(deformations, self.shield_threshold)
        self.shield_active = self.shield_level > 0.1
        
        # Mantém histórico limitado para economia de memória
        if len(self.history_deformation) > 1000:
            self.history_deformation = self.history_deformation[-1000:]
        self.history_deformation.extend(deformations.tolist())
        
        return {
            'deformation': deformations[-1],
            'shield_active': self.shield_active,
            'shield_level': self.shield_level
        }
