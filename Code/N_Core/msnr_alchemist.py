import numpy as np
import pandas as pd

class MSNRAlchemist:
    """
    MSNR-Alchemist (Market Structure Noise Reduction)
    Agente responsável por transmutar dados brutos em zonas de Ressonância Quântica.
    Funde conceitos de SMC, Fibonacci e Bollinger Bands.
    """
    
    def __init__(self, fibo_levels=[0.618, 0.786], bb_period=20, bb_std=2.0):
        self.fibo_levels = fibo_levels
        self.bb_period = bb_period
        self.bb_std = bb_std

    def calculate_resonance_zones(self, df):
        """
        Identifica a 'Zona de Ponto Zero' baseada na retração de impulsos.
        Lookback aumentado para 50 para capturar o movimento macro do fractal.
        """
        # Cálculo de Bandas de Bollinger (Contenção Plasmática)
        df['bb_mid'] = df['close'].rolling(window=self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_mid'] + (self.bb_std * df['bb_std'])
        df['bb_lower'] = df['bb_mid'] - (self.bb_std * df['bb_std'])
        
        # Identificação de Impulsos com Lookback de 50 candles
        lookback_impulse = 50
        last_high = df['high'].iloc[-lookback_impulse:].max()
        last_low = df['low'].iloc[-lookback_impulse:].min()
        diff = last_high - last_low
        
        zero_point_zones = {
            'bullish_entry': last_high - (diff * self.fibo_levels[1]), # 78.6%
            'bullish_optimal': last_high - (diff * self.fibo_levels[0]), # 61.8%
            'bearish_entry': last_low + (diff * self.fibo_levels[1]), # 78.6%
            'bearish_optimal': last_low + (diff * self.fibo_levels[0])  # 61.8%
        }
        
        return zero_point_zones

    def detect_fvgs(self, df, lookback=20):
        """
        Detecta Vácuos de Densidade (FVG).
        Retorna uma lista de zonas de desequilíbrio.
        """
        fvgs = []
        for i in range(len(df) - 2, len(df) - lookback, -1):
            # Bullish FVG (Gap entre a mínima da vela 1 e máxima da vela 3)
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                fvgs.append({'type': 'BULL_FVG', 'top': df['low'].iloc[i], 'bottom': df['high'].iloc[i-2]})
            
            # Bearish FVG (Gap entre a máxima da vela 1 e mínima da vela 3)
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                fvgs.append({'type': 'BEAR_FVG', 'top': df['low'].iloc[i-2], 'bottom': df['high'].iloc[i]})
        return fvgs

    def detect_sweeps(self, df):
        """
        Detecta Varreduras de Liquidez (Sweeps).
        Verifica se o preço rompeu um extremo recente e foi rejeitado com pavio.
        """
        curr = df.iloc[-1]
        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        
        # Extremos recentes (excluindo o candle atual)
        local_high = df['high'].iloc[-21:-1].max()
        local_low = df['low'].iloc[-21:-1].min()
        
        body = abs(curr['close'] - curr['open'])
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        
        sweep_detected = False
        
        # Bearish Sweep (Varrer topo e rejeitar)
        if curr['high'] > local_high and upper_wick > body:
            sweep_detected = "BEARISH_SWEEP"
        
        # Bullish Sweep (Varrer fundo e rejeitar)
        if curr['low'] < local_low and lower_wick > body:
            sweep_detected = "BULLISH_SWEEP"
            
        return sweep_detected

    def filter_noise(self, df, regime):
        """
        Aplica MSNR (Market Structure Noise Reduction).
        Valida se há 'Vácuo de Densidade' (FVG) à frente e PROTEGE contra Sweeps.
        """
        fvgs = self.detect_fvgs(df)
        sweep = self.detect_sweeps(df)
        
        if regime == 1: # BULL
            # Bloqueia se houver uma varredura de topo (rejeição de alta)
            if sweep == "BEARISH_SWEEP": return False
            return any(f['type'] == 'BULL_FVG' for f in fvgs)
            
        if regime == 2: # BEAR
            # Bloqueia se houver uma varredura de fundo (rejeição de baixa)
            if sweep == "BULLISH_SWEEP": return False
            return any(f['type'] == 'BEAR_FVG' for f in fvgs)
            
        return False

    def find_structural_targets(self, df_m5, df_m15, regime):
        """
        Busca alvos estruturais. Se em breakout, projeta via expansão.
        """
        curr_price = df_m5['close'].iloc[-1]
        atr = (df_m5['high'] - df_m5['low']).rolling(14).mean().iloc[-1]

        if regime == 1: # BULL
            range_high = df_m15['high'].iloc[-50:].max()
            # Se o preço já rompeu o topo do M15, projeta alvo de expansão
            if curr_price >= range_high - (atr * 0.5):
                target = curr_price + (atr * 4.0)
            else:
                target = range_high

            stop = df_m5['low'].iloc[-15:].min()
            if stop >= curr_price: stop = curr_price - (atr * 2.0)

        else: # BEAR
            range_low = df_m15['low'].iloc[-50:].min()
            if curr_price <= range_low + (atr * 0.5):
                target = curr_price - (atr * 4.0)
            else:
                target = range_low

            stop = df_m5['high'].iloc[-15:].max()
            if stop <= curr_price: stop = curr_price + (atr * 2.0)

        return target, stop

if __name__ == "__main__":
    print("MSNR-Alchemist: Sistema de Alquimia de Mercado Inicializado.")
