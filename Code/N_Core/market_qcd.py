import numpy as np
import pandas as pd

class MarketQCDTracker:
    """
    Market QCD (Quantum Chromodynamics) Tracker
    Modela o mercado sob a ótica da Força Forte Quântica.
    Foca no "Confinamento" de preços entre zonas de liquidez e na "Liberdade Assintótica" (rompimento explosivo).
    """
    
    def __init__(self, lookback_window: int = 20):
        self.lookback_window = lookback_window
        self.color_charges = {
            "RED": 0.0,   # Pressão de venda agressiva
            "GREEN": 0.0, # Pressão de compra agressiva
            "BLUE": 0.0   # Liquidez passiva (limit orders inferidas)
        }
        self.confinement_energy = 0.0
        self.asymptotic_threshold = 2.5 # Desvio padrão para fissão
        
    def calculate_color_charges(self, df: pd.DataFrame) -> tuple:
        """Calcula as 'Cargas de Cor' baseadas no fluxo das últimas barras."""
        # Simplificação heurística da carga de cor usando preço e volume
        recent = df.tail(self.lookback_window)
        
        # RED: Vendedores (fechamento < abertura) ponderado por volume
        red_charge = np.sum(np.where(recent['close'] < recent['open'], recent['tick_volume'], 0))
        
        # GREEN: Compradores (fechamento > abertura) ponderado por volume
        green_charge = np.sum(np.where(recent['close'] > recent['open'], recent['tick_volume'], 0))
        
        # BLUE: Liquidez passiva (somatório de pavios)
        upper_wicks = recent['high'] - np.maximum(recent['open'], recent['close'])
        lower_wicks = np.minimum(recent['open'], recent['close']) - recent['low']
        blue_charge = np.sum((upper_wicks + lower_wicks) * recent['tick_volume'])
        
        # Normalização
        total_charge = red_charge + green_charge + blue_charge + 1e-9
        self.color_charges["RED"] = red_charge / total_charge
        self.color_charges["GREEN"] = green_charge / total_charge
        self.color_charges["BLUE"] = blue_charge / total_charge
        
        return self.color_charges["RED"], self.color_charges["GREEN"], self.color_charges["BLUE"]
        
    def calculate_confinement_force(self, df: pd.DataFrame) -> float:
        """Calcula a Força Forte (Confinamento) baseada na distância para VWAP e densidade."""
        recent = df.tail(self.lookback_window).copy()
        
        # VWAP simplificada
        typical_price = (recent['high'] + recent['low'] + recent['close']) / 3
        vwap = np.sum(typical_price * recent['tick_volume']) / (np.sum(recent['tick_volume']) + 1e-9)
        
        current_price = recent['close'].iloc[-1]
        distance = abs(current_price - vwap)
        
        # Na QCD, a força de confinamento AUMENTA com a distância (até o rompimento)
        # F = k * r (Modelo de corda esticada)
        k_string_tension = np.std(recent['close']) + 1e-9
        self.confinement_energy = k_string_tension * distance
        
        return self.confinement_energy
        
    def detect_fission(self, df: pd.DataFrame) -> str:
        """Detecta se a energia rompeu o confinamento (Liberdade Assintótica)."""
        if len(df) < self.lookback_window:
            return "CONFINED"
            
        r, g, b = self.calculate_color_charges(df)
        confinement = self.calculate_confinement_force(df)
        
        # Volatilidade instantânea vs Histórica (tamanho do corpo direcional)
        recent_bodies = abs(df['close'].tail(self.lookback_window) - df['open'].tail(self.lookback_window))
        
        # O corpo atual deve ser massivo (ignoramos pavios)
        curr_open = df['open'].iloc[-1]
        curr_close = df['close'].iloc[-1]
        inst_vol = abs(curr_close - curr_open)
        
        # Filtro de ruído extremo e HFT
        valid_bodies = recent_bodies[recent_bodies > (np.mean(recent_bodies) * 0.5)]
        hist_vol = np.mean(valid_bodies) if len(valid_bodies) > 0 else (np.mean(recent_bodies) + 1e-9)
        
        kinetic_energy = inst_vol / (hist_vol + 1e-9)
        
        # Exigência MGD: Pelo menos 2.0x o tamanho médio de um corpo normal (raro, mas realístico)
        if kinetic_energy > 2.0:
            # Exigência de Alinhamento Vetorial: O movimento não pode ter deixado pavio contra a direção massiva
            total_range = df['high'].iloc[-1] - df['low'].iloc[-1]
            body_ratio = inst_vol / (total_range + 1e-9)
            
            # Corpo deve ser no mínimo 70% do tamanho da vela inteira (vela direcional sólida)
            if body_ratio > 0.70:
                if curr_close > curr_open:
                    return "FISSION_EXPANSION_UP"
                else:
                    return "FISSION_EXPANSION_DOWN"
                
        return f"CONFINED_E({confinement:.2f})"
