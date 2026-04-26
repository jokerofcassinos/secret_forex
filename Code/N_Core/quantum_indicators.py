import numpy as np
import pandas as pd

class QuantumIndicators:
    def __init__(self):
        pass

    @staticmethod
    def advanced_regime_score(df_slice, prev_score=0, prev_conf=0):
        """
        LÓGICA QUANTUM STITCHING (V11.1):
        Funde zonas próximas para manter a soberania do fluxo.
        """
        if len(df_slice) < 100: return 0, 0
        
        curr = df_slice.iloc[-1]
        prices = df_slice['close']
        
        # 1. Âncoras Soberanas
        ema21 = prices.ewm(span=21, adjust=False).mean().iloc[-1]
        ema100 = prices.ewm(span=100, adjust=False).mean().iloc[-1]
        
        # 2. Pivos de Inércia
        high_pivot = df_slice['high'].iloc[-8:-1].max()
        low_pivot = df_slice['low'].iloc[-8:-1].min()

        # --- MÁQUINA DE ESTADO COM FUSÃO ---

        # Se já estamos em BULL
        if prev_score == 1:
            # SÓ desliga se romper a EMA 100 (O Chão do Mercado)
            if curr['close'] < ema100:
                return 0, 0
            # Se apenas caiu abaixo da EMA 21 mas continua acima da 100, 
            # mantemos BULL com confiança reduzida (esperando a fusão)
            if curr['close'] < ema21:
                return 1, 50 
            return 1, 100

        # Se já estamos em BEAR
        if prev_score == 2:
            if curr['close'] > ema100:
                return 0, 0
            if curr['close'] > ema21:
                return 2, 50
            return 2, 100

        # --- GATILHOS DE IGNIÇÃO (Saindo do Neutro) ---
        if curr['close'] > high_pivot and curr['close'] > ema100:
            return 1, 100
            
        if curr['close'] < low_pivot and curr['close'] < ema100:
            return 2, 100

        return 0, 0 

    @staticmethod
    def calculate_rsi(prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))
