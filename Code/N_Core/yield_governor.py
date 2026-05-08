import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# [BOOTLOADER] Força reconhecimento dos binários Mingw64 e Engines C++
if os.name == 'nt':
    # 1. Mingw64 Binaries
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    
    # 2. NEXUS CPP Engines (bin)
    # yield_governor.py is in Code/N_Core, so we go up twice then Code/CPP_Engine/bin
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)
        if bin_path not in sys.path:
            sys.path.insert(0, bin_path)

# Importa o módulo C++ compilado
try:
    import cyt_engine as cyt_engine_module
except ImportError as e:
    raise RuntimeError(f"FALHA CRÍTICA: Motor CYT (C++) não encontrado na raiz. {e}")


class YieldGovernor:
    """
    Agente Yield-Governor v3.0: Ricci Flow + Soberania Continental.
    Especialista em detecção de colapsos invisíveis e supressão tática,
    com suporte à análise de volume da variedade (Determinante Métrica).
    """
    def __init__(self, shield_threshold=2.5, danger_window=10, danger_threshold=5.0):
        self.engine = cyt_engine_module.CYTEngine()
        self.shield_threshold = shield_threshold
        self.danger_window = danger_window
        self.danger_threshold = danger_threshold
        self.history_deformation = []
        self.shield_active = False
        self.shield_level = 0.0

    def monitor_topology(self, data_10d: np.ndarray):
        if data_10d.shape[0] != 10:
            raise ValueError("Matriz de entrada deve possuir 10 dimensões.")

        # 1. Processamento C++ (Ricci Flow v3.0)
        flow = self.engine.analyze_manifold_flow(data_10d)
        deformations = flow["deformation"]
        
        # 2. Avaliação de Escudo (Adaptado para v3.0)
        recent_avg = np.mean(deformations[-5:]) if len(deformations) >= 5 else 0.0
        
        if recent_avg > self.shield_threshold:
            self.shield_level = min(1.0, np.exp(recent_avg - self.shield_threshold) - 1.0)
        else:
            self.shield_level = 0.0
            
        self.shield_active = self.shield_level > 0.1
        
        return {
            'deformation': deformations[-1],
            'shield_active': self.shield_active,
            'shield_level': self.shield_level
        }

    def analyze_historical_danger(self, data_10d: np.ndarray):
        """
        Analisa todo o contexto histórico disponível e gera o mapa de zonas de perigo
        baseado na entropia topológica (Ricci Flow + Volume da Variedade).
        """
        if data_10d.shape[0] != 10:
            raise ValueError("Matriz de entrada deve possuir 10 dimensões.")
        
        return self.engine.calculate_danger_zones(data_10d, self.danger_window, self.danger_threshold)

    def detect_topological_trap(self, data_10d: np.ndarray, price_series: np.ndarray):
        """
        Detecta Divergência Topológica (Traps).
        Preço subindo mas Volume da Variedade (Determinante) colapsando.
        """
        flow = self.engine.analyze_manifold_flow(data_10d)
        determinants = flow["determinant"]
        
        if len(determinants) < 10: return "NORMAL"
        
        # Janela de 10 barras para medir divergência
        recent_prices = price_series[-10:]
        recent_dets = determinants[-10:]
        
        price_slope = np.polyfit(np.arange(10), recent_prices, 1)[0]
        det_slope = np.polyfit(np.arange(10), np.log1p(recent_dets), 1)[0]
        
        # BULL TRAP: Preço sobe, Determinante (Liquidez Topológica) desce
        if price_slope > 0 and det_slope < -0.05:
            return "BULL_TRAP"
        # BEAR TRAP: Preço desce, Determinante (Liquidez Topológica) sobe repentinamente (Fake crash)
        elif price_slope < 0 and det_slope > 0.05:
            return "BEAR_TRAP"
            
        return "NORMAL"

    def evaluate_dimensional_collapse(self, data_10d: np.ndarray):
        """
        Avalia se a malha topológica colapsou (Invalidando a tese estrutural).
        """
        if data_10d.shape[0] != 10: return {'is_collapsed': False}
        return self.engine.calculate_topological_collapse(data_10d)
