import numpy as np
import pandas as pd

class QuantumIndicators:
    def __init__(self):
        pass

    @staticmethod
    def calculate_resonance_zones(df_slice, atr_window=14):
        """
        TQFM v44 - Zonas de Ressonância Estacionária (S.R.Z)
        Mapeia "Muralhas de Interferência" baseadas em Choque Atômico.
        Retorna as caixas [BULL] e [BEAR] ativas.
        """
        if len(df_slice) < 50: return []
        
        # 1. Cálculo de ATR para escala
        high_low = df_slice['high'] - df_slice['low']
        high_close = np.abs(df_slice['high'] - df_slice['close'].shift(1))
        low_close = np.abs(df_slice['low'] - df_slice['close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(atr_window).mean().iloc[-1]
        
        zones = []
        # Percorre os últimos 100 candles para identificar zonas
        lookback = min(len(df_slice), 100)
        for i in range(len(df_slice) - lookback, len(df_slice)):
            candle = df_slice.iloc[i]
            body = abs(candle['close'] - candle['open'])
            
            # Identifica Choque Atômico (Ignition)
            if body > (atr * 1.1):
                zone_type = "BULL" if candle['close'] > candle['open'] else "BEAR"
                zone = {
                    "type": zone_type,
                    "top": max(candle['open'], candle['close']),
                    "bottom": min(candle['open'], candle['close']),
                    "start_idx": i,
                    "confidence": 1.0
                }
                
                # Verifica se a zona ainda é válida (não foi colapsada)
                is_active = True
                for j in range(i + 1, len(df_slice)):
                    test_candle = df_slice.iloc[j]
                    # Colapso: Fechamento fora da zona > 0.5 ATR
                    if zone_type == "BULL" and test_candle['close'] < zone['bottom'] - (atr * 0.5):
                        is_active = False; break
                    if zone_type == "BEAR" and test_candle['close'] > zone['top'] + (atr * 0.5):
                        is_active = False; break
                
                if is_active:
                    zones.append(zone)
        
        return zones

    @staticmethod
    def advanced_regime_score(df_slice, prev_score=0, prev_conf=0):
        """
        LÓGICA NEXUS-TQFM v43 (A Matriz de Fluxo / Flow Sovereignty):
        O ajuste terminal para cravamento de sombras e erradicação de micro-caixas.
        1. ZERO DELAY ATÔMICO: Removida a exigência de EMA 9 para Reversões Atômicas em 
           extremos de 40 velas. O sistema agora encerra o regime no tick exato da 
           sombra se houver choque institucional (>1.1x ATR).
        2. IMUNIDADE MATURADA: Tendências agora possuem 10 velas de imunidade (conf < 110) 
           contra colapsos triviais, garantindo Tsunamis contínuos e inquebráveis.
        3. NOISE GATE TERMINAL: Saída do Neutro exige spread de médias > 0.5x ATR, 
           aniquilando sequências de micro-caixas (flicker) em zonas de respiro.
        4. MOMENTUM LOCK: Um regime só colapsa se o momentum rápido (EMA 9/21) 
           tiver virado contra a tendência, impedindo fins precoces em pernadas fortes.
        """
        if len(df_slice) < 120: return 0, 0
        
        curr = df_slice.iloc[-1]

        # 1. Camadas de Fluxo e Momentum (EMAs)
        ema_fast = df_slice['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_mid = df_slice['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        ema_trend = df_slice['close'].ewm(span=34, adjust=False).mean().iloc[-1]
        ema_macro = df_slice['close'].ewm(span=89, adjust=False).mean().iloc[-1]
        
        ema_spread = abs(ema_fast - ema_mid)
        bull_momentum = (ema_fast > ema_mid)
        bear_momentum = (ema_fast < ema_mid)
        
        macro_bull = curr['close'] > ema_macro
        macro_bear = curr['close'] < ema_macro
        
        price_below_fast = curr['close'] < ema_fast
        price_above_fast = curr['close'] > ema_fast
        price_below_mid = curr['close'] < ema_mid
        price_above_mid = curr['close'] > ema_mid

        # 2. Dinâmica de Entropia (ATR)
        high_low = df_slice['high'] - df_slice['low']
        high_close = np.abs(df_slice['high'] - df_slice['close'].shift(1))
        low_close = np.abs(df_slice['low'] - df_slice['close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]

        # 3. Estruturas de Liquidez (TQFM v58: Ponto de Equilíbrio)
        swing_high_30 = df_slice['high'].iloc[-31:-1].max()
        swing_low_30 = df_slice['low'].iloc[-31:-1].min()
        high_10 = df_slice['high'].iloc[-11:-1].max()
        low_10 = df_slice['low'].iloc[-11:-1].min()
        
        local_high_20 = df_slice['high'].iloc[-21:-1].max()
        local_low_20 = df_slice['low'].iloc[-21:-1].min()
        abs_high_60 = df_slice['high'].iloc[-61:-1].max()
        abs_low_60 = df_slice['low'].iloc[-61:-1].min()

        # 4. Força Institucional
        is_green = curr['close'] > curr['open']
        is_red = curr['close'] < curr['open']
        body = abs(curr['close'] - curr['open'])
        is_strong = body > (atr * 0.5)
        is_ignition_shock = body > (atr * 0.9) 
        is_atomic = body > (atr * 1.1)
        is_super_atomic = body > (atr * 1.6)
        
        # Engulfing e Pivôs (TQFM v58)
        prev = df_slice.iloc[-2]
        bearish_engulfing = is_red and (prev['close'] > prev['open']) and (curr['open'] >= prev['close']) and (curr['close'] < prev['open'])
        bullish_engulfing = is_green and (prev['close'] < prev['open']) and (curr['open'] <= prev['close']) and (curr['close'] > prev['open'])
        
        # 5. Gatilhos Atômicos (TQFM v58: Sincronia Fractal)
        recent_max = df_slice['high'].iloc[-3:-1].max()
        recent_min = df_slice['low'].iloc[-3:-1].min()
        
        is_abs_top = (recent_max >= abs_high_60 - (atr * 0.1))
        is_abs_bottom = (recent_min <= abs_low_60 + (atr * 0.1))
        is_local_top = (recent_max >= local_high_20 - (atr * 0.1))
        is_local_bottom = (recent_min <= local_low_20 + (atr * 0.1))
        
        is_bull_ignition = (curr['close'] > high_10) and is_atomic and bull_momentum
        is_bear_ignition = (curr['close'] < low_10) and is_atomic and bear_momentum

        # Rejeição por Sombra
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        is_exhaustion_top = is_local_top and ((upper_wick > body * 1.5 and is_red) or (upper_wick > body * 3.0))
        is_exhaustion_bottom = is_local_bottom and ((lower_wick > body * 1.5 and is_green) or (lower_wick > body * 3.0))

        # Trava de Estiramento (Anti-Fomo)
        dist_mid = abs(curr['close'] - ema_mid)
        is_overextended = dist_mid > (atr * 1.8) # Mais folga para parábolas

        # GATILHOS FINAIS
        dist_macro = abs(curr['close'] - ema_macro)
        is_momentum_explosion_bull = is_super_atomic and is_green and bull_momentum
        is_momentum_explosion_bear = is_super_atomic and is_red and bear_momentum

        # SOBERANIA MACRO (Influência, não proibição)
        is_macro_bull = (ema_fast > ema_macro)
        is_macro_bear = (ema_fast < ema_macro)

        # Gatilhos de INÍCIO
        can_start_bull = (is_abs_bottom and dist_macro > atr * 1.2) or (is_local_bottom and is_macro_bull) or (is_bull_ignition and is_macro_bull) or is_momentum_explosion_bull
        start_atomic_bottom = can_start_bull and (not is_overextended) and (is_green and (is_atomic or is_strong) or is_exhaustion_bottom)
        
        can_start_bear = is_abs_top or (is_local_top and is_macro_bear) or (is_bear_ignition and is_macro_bear) or is_momentum_explosion_bear
        start_atomic_top = can_start_bear and (is_red and (is_atomic or is_strong) or is_exhaustion_top)

        # Gatilhos de FLIP (Inversão Direta)
        flip_to_bear = (is_red and is_super_atomic) or (curr['close'] < swing_low_30 and is_red and is_atomic)
        flip_to_bull = (is_green and is_super_atomic) or (curr['close'] > swing_high_30 and is_green and is_atomic)

        # --- MÁQUINA DE ESTADO TQFM v58 (SINCRONIA FRACTAL) ---
        
        # ESTADO BULL (1)
        if prev_score == 1:
            if flip_to_bear: return 2, 100
            if is_red and is_super_atomic: return 0, -2
            
            # Se o pivô de 30 velas estiver intacto, mantém BULL
            if curr['close'] >= swing_low_30:
                return 1, min(prev_conf + 1, 150)
            
            if (curr['close'] < ema_trend) and (not bull_momentum) and (prev_conf > 30):
                return 0, -2
            
            return 1, min(prev_conf + 1, 150)
            
        # ESTADO BEAR (2)
        if prev_score == 2:
            if flip_to_bull: return 1, 100
            if is_green and is_super_atomic: return 0, -2
            
            if curr['close'] <= swing_high_30:
                return 2, min(prev_conf + 1, 150)
                
            if (curr['close'] > ema_trend) and (not bear_momentum) and (prev_conf > 30):
                return 0, -2
            
            return 2, min(prev_conf + 1, 150)

        # --- ESTADO NEUTRO (0) ---
        if prev_conf < 0: return 0, prev_conf + 1
            
        if start_atomic_top: return 2, 100
        if start_atomic_bottom: return 1, 100
        
        # Saída do Neutro: Ignição Simples
        high_5 = df_slice['high'].iloc[-6:-1].max()
        low_5 = df_slice['low'].iloc[-6:-1].min()
        
        if is_green and is_strong and (curr['close'] > high_5) and bull_momentum: 
            return 1, 100
        if is_red and is_strong and (curr['close'] < low_5) and bear_momentum: 
            return 2, 100

        return 0, 0

    @staticmethod
    def calculate_rsi(prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))
