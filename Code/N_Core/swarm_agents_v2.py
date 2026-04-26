import numpy as np
import pandas as pd

class EukleidisAgent:
    """Especialista em Geometria Fractal (Curvatura de Preço)"""
    def __init__(self):
        self.id = "EUKLEIDIS_001"

    def analyze_curvature(self, prices):
        """Mede a aceleração angular do movimento."""
        if len(prices) < 10: return 1.0
        
        # 1. Calcular a inclinação (slope) atual e anterior
        x = np.arange(5)
        slope_now = np.polyfit(x, prices.tail(5).values, 1)[0]
        slope_prev = np.polyfit(x, prices.iloc[-10:-5].values, 1)[0]
        
        # 2. VPI Score: Razão entre as inclinações
        # Se o preço está subindo, mas a inclinação atual é menor que a anterior -> Curvatura Negativa
        vpi = slope_now / (slope_prev + 1e-9)
        return vpi

class PhantasmaAgent:
    """O Caçador de Armadilhas (Liquidez Fantasma)"""
    def __init__(self):
        self.id = "PHANTASMA_001"

    def detect_trap_risk(self, df_slice, regime):
        """Identifica se o sinal ocorre em uma zona de 'Stop Hunt'."""
        if len(df_slice) < 20: return False
        
        # 1. Identificar Topos/Fundos Triplos (Zonas de Isca)
        highs = df_slice['high'].tail(20)
        lows = df_slice['low'].tail(20)
        
        # Se o preço está muito perto de um topo anterior sem rompê-lo com força
        # É provável que haja uma armadilha de liquidez ali.
        if regime == "BULL":
            recent_peak = highs.iloc[:-1].max()
            if abs(df_slice['close'].iloc[-1] - recent_peak) < (df_slice['close'].iloc[-1] * 0.0005):
                return True # Risco de Armadilha (Double Top)
                
        if regime == "BEAR":
            recent_floor = lows.iloc[:-1].min()
            if abs(df_slice['close'].iloc[-1] - recent_floor) < (df_slice['close'].iloc[-1] * 0.0005):
                return True
                
        return False
