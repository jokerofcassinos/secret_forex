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
    def calculate_rsi(prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_tactical_dots(df, regime_score):
        """
        Gera sinais visuais (dots) ultra-dinâmicos com filtros de exaustão e gravidade.
        0: Neutro (Cinza) - Fase de transição ou exaustão.
        1: Compra Sniper (Verde) - Regime Bull + Correção Saudável + Momentum de Retorno.
        2: Venda Sniper (Vermelho) - Regime Bear + Repique de Exaustão + Momentum de Queda.
        """
        if len(df) < 50: return [0] * len(df)
        
        # 1. Camadas de Inteligência
        ema_fast = df['close'].ewm(span=9, adjust=False).mean()
        ema_mid = df['close'].ewm(span=21, adjust=False).mean()
        ema_trend = df['close'].ewm(span=34, adjust=False).mean()
        ema_macro = df['close'].ewm(span=89, adjust=False).mean()
        rsi = QuantumIndicators.calculate_rsi(df['close'], 14)
        
        # Cálculo de Volatilidade para Trava de Gravidade
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean()
        
        dots = []
        for i in range(len(df)):
            if i < 14:
                dots.append(0)
                continue
                
            curr_regime = regime_score[i]
            c = df['close'].iloc[i]
            o = df['open'].iloc[i]
            h = df['high'].iloc[i]
            l = df['low'].iloc[i]
            
            curr_rsi = rsi.iloc[i]
            prev_rsi = rsi.iloc[i-1]
            curr_e9 = ema_fast.iloc[i]
            curr_e21 = ema_mid.iloc[i]
            curr_e34 = ema_trend.iloc[i]
            curr_e89 = ema_macro.iloc[i]
            curr_atr = atr.iloc[i]
            
            # --- FILTROS DE SEGURANÇA NEXUS v2.1 ---
            
            # 1. Trava de Gravidade (Anti-Estiramento)
            # Se o preço estiver a mais de 2.0 ATRs da média 89, está "caro" demais.
            dist_macro = abs(c - curr_e89)
            is_overextended = dist_macro > (curr_atr * 2.0)
            
            # 2. Filtro de Momentum (Velas)
            is_green_candle = c > o
            is_red_candle = c < o
            
            # 3. Filtro de Exaustão RSI
            rsi_rising = curr_rsi > prev_rsi
            rsi_falling = curr_rsi < prev_rsi
            
            dot = 0 # Neutro (Cinza)
            
            # --- LÓGICA DE COMPRA SNIPER (GREEN DOT) ---
            if curr_regime == 1: # Tsunami Bull
                # Condições: 
                # A) Não pode estar sobre-estendido (caro)
                # B) Deve estar em fase de correção (perto da EMA 21 ou 34)
                # C) O RSI deve estar voltando a subir (gatilho de momentum) ou em sobrevenda técnica (<45)
                # D) O candle atual deve mostrar força compradora (verde)
                
                near_support = (c <= curr_e21 * 1.001) # Perto ou abaixo da EMA 21
                if not is_overextended and near_support:
                    if (curr_rsi < 50 and rsi_rising) or (curr_rsi < 40):
                        if is_green_candle:
                            dot = 1 # VERDE: Compra de Alta Probabilidade
            
            # --- LÓGICA DE VENDA SNIPER (RED DOT) ---
            elif curr_regime == 2: # Tsunami Bear
                # Condições:
                # A) Não pode estar sobre-estendido (longe da 89 p/ baixo)
                # B) Deve estar em fase de repique (perto da EMA 21 ou 34)
                # C) RSI voltando a cair ou em sobrecompra técnica (>55)
                # D) Candle atual deve ser vermelho
                
                near_resistance = (c >= curr_e21 * 0.999) # Perto ou acima da EMA 21
                if not is_overextended and near_resistance:
                    if (curr_rsi > 50 and rsi_falling) or (curr_rsi > 60):
                        if is_red_candle:
                            dot = 2 # VERMELHO: Venda de Alta Probabilidade
            
            dots.append(dot)
        
        return dots
