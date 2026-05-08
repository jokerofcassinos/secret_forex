import numpy as np
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
    import qrw_engine
except ImportError as e:
    print(f"WARNING: qrw_engine C++ module not found. Error: {e}")

class QRWTracker:
    """
    N-Core Agent: Quantum Random Walk (QRW) v3.2 - Predictive Engine
    Mapeia a densidade de probabilidade futura e detecta a exaustão quântica (Singularidade).
    Transforma o QRW de um gerador de sinais em um motor de mapeamento de realidade.
    """
    def __init__(self, positions=401):
        try:
            self.engine = qrw_engine.QRWEngine(positions)
            self.is_active = True
        except NameError:
            self.is_active = False
            
        self.num_positions = positions
        self.last_skew = 0.0
        self.last_entropy = 0.0
        self.last_variance = 0.0
        self.scale_factor = 0.005 # Calibração para GER40

    def process_market_slice(self, df_slice):
        """
        Evolui a função de onda com base no fluxo de preços real.
        Extrai as métricas de assimetria e coerência.
        """
        if not self.is_active or len(df_slice) < 50:
            return 0.0, "OFFLINE"

        deltas = df_slice['close'].diff().fillna(0).values[-50:]
        volumes = df_slice['tick_volume'].values[-50:]
        
        # Evolução quântica no Metal (C++)
        self.last_skew = self.engine.update_and_get_skew(deltas, volumes, self.scale_factor)
        
        # Mapeamento de Regimes Quânticos
        # Skewness > 0.08 indica acúmulo Bull
        # Skewness < -0.08 indica distribuição Bear
        signal = "QUANTUM_STABILITY"
        if self.last_skew > 0.08: signal = "QUANTUM_ACCUMULATION_BULL"
        elif self.last_skew < -0.08: signal = "QUANTUM_DISTRIBUTION_BEAR"
        
        return self.last_skew, signal

    def project_future_horizon(self, current_price, atr, plasma_zones, simulations=500):
        """
        Utiliza o motor C++ para 'ver o futuro' e detectar colapsos eminentes.
        """
        if not self.is_active:
            return []

        # Chama a simulação de massa no C++
        breaches = self.engine.simulate_future_collapse(
            current_price, 
            atr, 
            steps=40, 
            simulations=simulations,
            top_zone=plasma_zones['top_level'],
            bottom_zone=plasma_zones['bottom_level'],
            threshold_mult=1.5
        )
        
        return breaches

    def get_probability_cloud(self):
        """
        Retorna a nuvem de probabilidade atualizada para renderização no HUD.
        """
        if not self.is_active: return []
        return self.engine.get_probability_distribution()

    def detect_singularity_exhaustion(self, current_price):
        """
        Identifica se a função de onda atingiu um ponto de singularidade 
        onde o preço deve colapsar de volta à média.
        """
        if not self.is_active: return "NEUTRAL"
        
        # Se a assimetria for extrema e a coerência cair, temos uma Singularidade
        if self.last_skew > 0.15: return "QUANTUM_EXHAUSTION_SHORT"
        if self.last_skew < -0.15: return "QUANTUM_EXHAUSTION_LONG"
        
        return "NEUTRAL"

if __name__ == "__main__":
    print("QRW Predictive Engine v3.2 - Carregado com Sucesso.")