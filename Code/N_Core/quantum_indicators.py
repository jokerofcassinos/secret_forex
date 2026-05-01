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
        ema_gravity = df_slice['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        ema_spread = abs(ema_fast - ema_mid)
        bull_momentum = (ema_fast > ema_mid)
        bear_momentum = (ema_fast < ema_mid)
        
        # Filtros de Gravidade
        under_gravity = curr['close'] < ema_gravity
        above_gravity = curr['close'] > ema_gravity
        
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

        # 3. Estruturas de Liquidez (TQFM v75: Colapso de Sombra)
        swing_high_20 = df_slice['high'].iloc[-21:-1].max()
        swing_low_20 = df_slice['low'].iloc[-21:-1].min()
        high_10 = df_slice['high'].iloc[-11:-1].max()
        low_10 = df_slice['low'].iloc[-11:-1].min()
        
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
        
        # Engulfing e Pivôs (TQFM v75)
        prev = df_slice.iloc[-2]
        bearish_engulfing = is_red and (prev['close'] > prev['open']) and (curr['open'] >= prev['close']) and (curr['close'] < prev['open'] - (atr * 0.1))
        bullish_engulfing = is_green and (prev['close'] < prev['open']) and (curr['open'] <= prev['close']) and (curr['close'] > prev['open'] + (atr * 0.1))
        
        # 5. Gatilhos Atômicos (TQFM v75: Singularidade de Fluxo)
        recent_max = df_slice['high'].iloc[-3:-1].max()
        recent_min = df_slice['low'].iloc[-3:-1].min()
        
        # Extremos de Longo Prazo e Locais
        abs_high_120 = df_slice['high'].iloc[-121:-1].max()
        abs_low_120 = df_slice['low'].iloc[-121:-1].min()
        local_high_20 = df_slice['high'].iloc[-21:-1].max()
        local_low_20 = df_slice['low'].iloc[-21:-1].min()
        
        is_abs_top = (curr['high'] >= abs_high_120 - (atr * 0.05))
        is_abs_bottom = (curr['low'] <= abs_low_120 + (atr * 0.05))
        is_local_top = (recent_max >= local_high_20 - (atr * 0.1))
        is_local_bottom = (recent_min <= local_low_20 + (atr * 0.1))
        
        # SINGULARIDADE ATÔMICA (ARS): Reversão Imediata em Extremos
        is_atomic_rebound_bull = is_abs_bottom and is_green and (is_atomic or is_strong)
        is_atomic_rebound_bear = is_abs_top and is_red and (is_atomic or is_strong)

        is_bull_ignition = (curr['close'] > high_10) and is_atomic and bull_momentum
        is_bear_ignition = (curr['close'] < low_10) and is_atomic and bear_momentum

        # Rejeição por Sombra (Rigor Estabilizado v76)
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        
        # Só exaustão se o candle for contrário (Vermelho em Topo, Verde em Fundo) E sombra expressiva
        is_exhaustion_top = is_local_top and is_red and (upper_wick > body * 2.0 or upper_wick > atr * 0.8)
        is_exhaustion_bottom = is_local_bottom and is_green and (lower_wick > body * 2.0 or lower_wick > atr * 0.8)

        # Trava de Estiramento (Anti-Fomo)
        dist_mid = abs(curr['close'] - ema_mid)
        is_overextended = dist_mid > (atr * 1.8) 

        # GATILHOS FINAIS
        dist_macro = abs(curr['close'] - ema_macro)
        is_momentum_explosion_bull = is_super_atomic and is_green and bull_momentum
        is_momentum_explosion_bear = is_super_atomic and is_red and bear_momentum

        # SOBERANIA MACRO
        is_macro_bull = (ema_fast > ema_macro)
        is_macro_bear = (ema_fast < ema_macro)

        # Gatilhos de INÍCIO (v76: Estabilizado)
        can_start_bull = is_atomic_rebound_bull or (is_abs_bottom and dist_macro > atr * 1.5) or (is_bull_ignition and is_macro_bull) or is_momentum_explosion_bull
        start_atomic_bottom = can_start_bull and (not is_overextended) and (is_green and is_atomic or is_exhaustion_bottom)
        
        can_start_bear = is_atomic_rebound_bear or (is_abs_top and dist_macro > atr * 1.5) or (is_bear_ignition and is_macro_bear) or is_momentum_explosion_bear
        start_atomic_top = can_start_bear and (is_red and is_atomic or is_exhaustion_top)

        # Gatilhos de FLIP (Inversão Direta v85)
        flip_to_bear = (is_red and is_super_atomic and bear_momentum) or (curr['close'] < swing_low_20 and is_red and is_atomic)
        flip_to_bull = (is_green and is_super_atomic and bull_momentum) or (curr['close'] > swing_high_20 and is_green and is_atomic)

        # --- MÁQUINA DE ESTADO TQFM v400 (THE ABSOLUTE MACRO MONOLITH) ---
        
        # O Ruído intradiário (pullbacks) afeta as EMAs curtas (9, 21) constantemente.
        # Para criar o Monólito Perfeito, a Caixa agora é ancorada diretamente na Gravidade Macro (89).

        # 1. Filtro de Massa de Elite
        body = abs(curr['close'] - curr['open'])
        is_significant = body > (atr * 0.8)
        
        # 2. O Grande Colisor (MACRO FLIP)
        # O regime só inverte naturalmente se a Tendência (34) cruzar a Macro (89).
        # Isso garante que um pullback precisa durar horas para quebrar o monólito.
        macro_reversal_bull = (ema_trend > ema_macro)
        macro_reversal_bear = (ema_trend < ema_macro)
        
        # 3. Gatilho de Velocidade Sideral (V-Shape Macro)
        # Se houver um choque violento, antecipamos o flip usando a EMA 21 em vez da 34,
        # MAS ela ainda deve obrigatoriamente cruzar a MACRO (89).
        speed_bypass_bull = (ema_mid > ema_macro) and is_green and (body > atr * 1.5)
        speed_bypass_bear = (ema_mid < ema_macro) and is_red and (body > atr * 1.5)

        # 4. Imunidade de Regime Absoluta
        # O regime é literalmente cego para oscilações nas primeiras 20 velas.
        is_mature = (prev_conf > 20)

        # ESTADO BULL (1)
        if prev_score == 1:
            if is_mature:
                # FLIP MACRO: A maré de longo prazo virou
                if macro_reversal_bear:
                    return 2, 100
                    
                # FLIP DE VELOCIDADE: Mergulho V-Shape cruzando a Macro
                if speed_bypass_bear:
                    return 2, 100

            # Monólito - Imune a todas as médias curtas. Segue a Macro 89.
            return 1, min(prev_conf + 1, 50000)

        # ESTADO BEAR (2)
        if prev_score == 2:
            if is_mature:
                # FLIP MACRO: A maré de longo prazo virou
                if macro_reversal_bull:
                    return 1, 100
                    
                # FLIP DE VELOCIDADE: Rali V-Shape cruzando a Macro
                if speed_bypass_bull:
                    return 1, 100

            # Monólito - Imune a todas as médias curtas. Segue a Macro 89.
            return 2, min(prev_conf + 1, 50000)

        # NOISE GATE v400
        if not is_significant: return 0, 0
        
        if macro_reversal_bull: return 1, 50
        if macro_reversal_bear: return 2, 50

        if speed_bypass_bull: return 1, 100
        if speed_bypass_bear: return 2, 100

        return 0, 0

    @staticmethod
    def calculate_regime_health(df):
        """
        Calcula a saúde da tendência (0-100%).
        Baseado na divergência entre EMA 34 (Tendência) e EMA 89 (Macro).
        """
        if len(df) < 90: return 100
        ema_34 = df['close'].ewm(span=34, adjust=False).mean()
        ema_89 = df['close'].ewm(span=89, adjust=False).mean()
        
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        
        gap = abs(ema_34.iloc[-1] - ema_89.iloc[-1])
        health = min(100, (gap / (atr * 4.0)) * 100)
        return int(health)

    @staticmethod
    def calculate_rsi(prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_tactical_dots(df, regime_score):
        """
        Gera sinais visuais (dots) v27.1 (The Entropy Guard - Strict).
        Foco: Silêncio total em zonas de exaustão e transição.
        """
        if len(df) < 60: return [0] * len(df)
        
        # Camadas de Comando
        ema_9 = df['close'].ewm(span=9, adjust=False).mean()
        ema_21 = df['close'].ewm(span=21, adjust=False).mean()
        ema_34 = df['close'].ewm(span=34, adjust=False).mean()
        ema_89 = df['close'].ewm(span=89, adjust=False).mean()
        
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean()
        
        dots = []
        lookback = 8
        for i in range(len(df)):
            if i < 20:
                dots.append(0); continue
                
            curr_r = regime_score[i]
            c = df['close'].iloc[i]
            o = df['open'].iloc[i]
            h = df['high'].iloc[i]
            l = df['low'].iloc[i]
            e9 = ema_9.iloc[i]
            e21 = ema_21.iloc[i]
            e34 = ema_34.iloc[i]
            e89 = ema_89.iloc[i]
            curr_atr = atr.iloc[i]
            
            # --- CÁLCULO DE ENTROPIA LOCAL ---
            gap_macro = abs(e34 - e89) / (curr_atr + 1e-9)
            gap_fast = abs(e9 - e21) / (curr_atr + 1e-9)
            
            # TRAVA DE SEGURANÇA Ph.D.
            # Se a saúde macro é baixa (<20%) ou as médias estão coladas, SILÊNCIO.
            is_exhausted = (gap_macro < 0.6) or (gap_fast < 0.1)
            
            dot = 0 # Default: Cinza (Será filtrado pelo gradiente)
            
            if not is_exhausted:
                l_max = df['high'].iloc[i-lookback:i+1].max()
                l_min = df['low'].iloc[i-lookback:i+1].min()
                p_rel = (c - l_min) / (l_max - l_min + 1e-9)
                
                # --- LÓGICA BASE ---
                if curr_r == 1 and p_rel < 0.50 and (l <= e9 * 1.001) and (c > o):
                    dot = 1
                elif curr_r == 2 and p_rel > 0.50 and (h >= e9 * 0.999) and (c < o):
                    dot = 2
            
            dots.append(dot)
            
        # --- GRADIENTE PASS ---
        gradient_dots = [0] * len(dots)
        for i in range(len(dots)):
            if dots[i] == 1:
                gradient_dots[i] = 1
                if i+1 < len(dots): gradient_dots[i+1] = 11
                if i+2 < len(dots): gradient_dots[i+2] = 12
                if i+3 < len(dots): gradient_dots[i+3] = 13
            elif dots[i] == 2:
                gradient_dots[i] = 2
                if i+1 < len(dots): gradient_dots[i+1] = 21
                if i+2 < len(dots): gradient_dots[i+2] = 22
                if i+3 < len(dots): gradient_dots[i+3] = 23
        return gradient_dots
