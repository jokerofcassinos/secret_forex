import numpy as np
import pandas as pd
import sys
import os

# --- NEXUS QDD BRIDGE ---
if sys.platform == 'win32':
    # Garante carregamento das DLLs do MinGW
    mingw_bin = r"D:\msys64\mingw64\bin"
    if os.path.exists(mingw_bin):
        try:
            os.add_dll_directory(mingw_bin)
        except Exception: pass

# Localiza extensões C++
# Agora os binários residem na raiz do projeto, então importações diretas funcionam.


from Code.N_Core.quantum_phase_transition import QuantumPhaseTransition

try:
    import qdd_engine
    import qho_engine
    _QDD_ENGINE_INST = qdd_engine.QDDEngine(1, 1.0, 0.05)
    _QHO_ENGINE_INST = qho_engine.QHOEngine()
    QDD_AVAILABLE = True
except ImportError:
    _QDD_ENGINE_INST = None
    _QHO_ENGINE_INST = None
    QDD_AVAILABLE = False

class QuantumIndicators:
    def __init__(self):
        self.qpt = QuantumPhaseTransition()

    @staticmethod
    def _get_qdd_regime_with_direction(data_series, timeframe_period=16386, atr=1.0, window=34, pti=0.0):
        """
        Internal helper v22.0 PHASE SYNC MODE:
        - window=8 (Ignition): WMA(5), uv_cutoff=1.
        - window=34 (Stability): SMA(34), uv_cutoff=3.
        - Histerese Dinâmica: Encolhe para 0.01 ATR se PTI > 0.80.
        """
        if not QDD_AVAILABLE or len(data_series) < window:
            return 0, 0
        
        uv_cutoff = 3 if window >= 32 else 1
        energy_mult = 0.03
        
        if timeframe_period <= 1: energy_mult = 0.05
        elif timeframe_period <= 5: energy_mult = 0.04
            
        arr = np.array(data_series.tail(window), dtype=np.float64)
        try:
            res = _QDD_ENGINE_INST.quantize_regime(arr, uv_cutoff, energy_threshold=atr*energy_mult)
            state = res['regime_state']
            
            direction = 0
            if state >= 1:
                # ADAPTIVE HYSTERESIS (v21.0)
                # Se PTI elevado, sensibilidade máxima para captura de pivot
                if pti > 0.80:
                    hyst = atr * 0.01
                elif window < 10:
                    hyst = atr * 0.03
                else:
                    hyst = atr * 0.05
                
                if window < 10:
                    weights = np.arange(1, 6)
                    subset = data_series.tail(5)
                    pivot = (subset.values * weights).sum() / weights.sum()
                else:
                    pivot = data_series.tail(window).mean()
                
                curr_price = data_series.iloc[-1]
                if curr_price > pivot + hyst: direction = 1
                elif curr_price < pivot - hyst: direction = 2
                else: direction = 1 if curr_price > pivot else 2
                
            return state, direction
        except Exception:
            return 0, 0

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

    def advanced_regime_score(self, df_slice, prev_score=0, prev_conf=0, q_math_data=None, debug=False):
        """
        LÓGICA NEXUS-TQFM v220 (INCOMPRESSIBILIDADE DE FLUXO / MONÓLITO ABSOLUTO):
        1. TENSÃO SUPERFICIAL: Proíbe flips sem cruzamento da EMA 34.
        2. FILTRO DE CONTRA-FLUXO: Se health > 50%, ignora sinais contra EMA 89.
        3. MONÓLITO TOTAL: r_conf sempre incremental se score for mantido.
        4. FORÇA BRUTA: Flip instantâneo se Body > 1.5x ATR (Ignora Lock).
        """
        if len(df_slice) < 120: 
            return (0, 0, {}) if debug else (0, 0)
        
        curr = df_slice.iloc[-1]
        atr = (df_slice['high'] - df_slice['low']).rolling(14).mean().iloc[-1]
        health = QuantumIndicators.calculate_regime_health(df_slice)

        # 1. Camadas de Fluxo
        ema_fast = df_slice['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_trend = df_slice['close'].ewm(span=34, adjust=False).mean().iloc[-1]
        ema_macro = df_slice['close'].ewm(span=89, adjust=False).mean().iloc[-1]
        ema_gravity = df_slice['close'].ewm(span=200, adjust=False).mean().iloc[-1]

        # 2. DECODE MEMÓRIA v4.0
        if prev_score == 0:
            last_polar = prev_conf // 100000000
            last_dur = (prev_conf % 100000000) // 100
            bars_neutral = prev_conf % 100
        else:
            last_polar, last_dur, bars_neutral = prev_score, prev_conf, 0

        # 3. Anomalia Quântica (PTI)
        pti = 0.0; qpt_rec = "STABLE"
        if q_math_data: pti, qpt_rec = self.qpt.evaluate_transition(df_slice, prev_score, q_math_data)
        
        # 4. Pavio de Ignição & Extremos (20b)
        local_high_20 = df_slice['high'].iloc[-21:-1].max()
        local_low_20 = df_slice['low'].iloc[-21:-1].min()
        
        body = abs(curr['close'] - curr['open'])
        is_brute_force = body > (atr * 1.5)
        
        is_breakout_bull = curr['close'] > local_high_20 and curr['close'] > ema_fast
        is_breakout_bear = curr['close'] < local_low_20 and curr['close'] < ema_fast
        
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        wick_rejection_bull = (curr['low'] <= local_low_20) and (lower_wick > body * 1.5)
        wick_rejection_bear = (curr['high'] >= local_high_20) and (upper_wick > body * 1.5)

        # 5. DUAL-QDD PURIFICATION (v22.0 Incompressível)
        _, qdd_ign = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'], 16386, atr, window=8, pti=pti)
        _, qdd_ign_p1 = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'].iloc[:-1], 16386, atr, window=8, pti=pti)
        _, qdd_stab = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'], 16386, atr, window=34, pti=pti)
        _, qdd_p1 = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'].iloc[:-1], 16386, atr, window=34, pti=pti)
        _, qdd_p2 = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'].iloc[:-2], 16386, atr, window=34, pti=pti)

        # 6. FILTRO DE CONTRA-FLUXO (v22.0)
        # Se Health > 50%, sinais contra a EMA 89 são ignorados a menos que PTI seja crítico
        if health > 50 and pti < 0.99:
            if curr['close'] > ema_macro: # Tendência Bull
                if qdd_stab == 2: qdd_stab = 0
                if qdd_ign == 2: qdd_ign = 0
            elif curr['close'] < ema_macro: # Tendência Bear
                if qdd_stab == 1: qdd_stab = 0
                if qdd_ign == 1: qdd_ign = 0

        # 7. Gravity Block com Bypass v21.0
        has_bypass = (pti > 0.95) or (body > atr * 1.2) or is_breakout_bull or is_breakout_bear or is_brute_force
        gravity_bull_block = (curr['close'] < ema_gravity) and not has_bypass and not wick_rejection_bull
        gravity_bear_block = (curr['close'] > ema_gravity) and not has_bypass and not wick_rejection_bear

        # 8. Máquina de Estado v22.0 (INCOMPRESSIBILIDADE)
        r_score, r_conf = 0, 0
        effective_qdd = qdd_stab if prev_score != 0 else qdd_ign
        
        debug_data = {
            "pti": pti, "qdd_dir": effective_qdd, "health": health,
            "gravity_bull_block": gravity_bull_block, "gravity_bear_block": gravity_bear_block,
            "ema_trend": ema_trend, "ema_macro": ema_macro, "last_polar": last_polar
        }

        # A. OVERRIDES DE SINGULARIDADE
        if pti > 0.98 or qpt_rec == "IMMEDIATE_PHASE_FLIP":
            target = 1 if qdd_ign == 1 else (2 if qdd_ign == 2 else 0)
            if target != 0 and ((target == 1 and not gravity_bull_block) or (target == 2 and not gravity_bear_block)):
                r_score = target; r_conf = (prev_conf + 1) if prev_score == target else 1
            else:
                r_score = 0
                r_conf = (last_polar * 100000000) + (min(last_dur, 999999) * 100) + min(bars_neutral + 1, 99)

        # ESTADO BULL (1)
        elif prev_score == 1:
            # TENSÃO SUPERFICIAL: Proíbe flip para Bear se preço acima da EMA 34
            flip_to_bear = (qdd_stab == 2 and qdd_p1 == 2 and qdd_p2 == 2) or (pti > 0.95) or (is_brute_force and curr['close'] < ema_trend)
            if curr['close'] > ema_trend and not (pti > 0.99 or is_brute_force):
                flip_to_bear = False
                
            exit_denied = (health > 30) and (not flip_to_bear) and (curr['close'] > ema_macro)
            
            if exit_denied or (curr['close'] > ema_macro and qdd_stab == 1):
                r_score, r_conf = 1, prev_conf + 1
            else:
                can_exit = flip_to_bear or (pti > 0.92) or (curr['close'] < ema_macro)
                if can_exit: 
                    if flip_to_bear and not gravity_bear_block: r_score, r_conf = 2, 1
                    else: r_score, r_conf = 0, (1 * 100000000) + (min(prev_conf, 999999) * 100) + 1
                else: r_score, r_conf = 1, prev_conf + 1

        # ESTADO BEAR (2)
        elif prev_score == 2:
            flip_to_bull = (qdd_stab == 1 and qdd_p1 == 1 and qdd_p2 == 1) or (pti > 0.95) or (is_brute_force and curr['close'] > ema_trend)
            if curr['close'] < ema_trend and not (pti > 0.99 or is_brute_force):
                flip_to_bull = False

            exit_denied = (health > 30) and (not flip_to_bull) and (curr['close'] < ema_macro)
            
            if exit_denied or (curr['close'] < ema_macro and qdd_stab == 2):
                r_score, r_conf = 2, prev_conf + 1
            else:
                can_exit = flip_to_bull or (pti > 0.92) or (curr['close'] > ema_macro)
                if can_exit:
                    if flip_to_bull and not gravity_bull_block: r_score, r_conf = 1, 1
                    else: r_score, r_conf = 0, (2 * 100000000) + (min(prev_conf, 999999) * 100) + 1
                else: r_score, r_conf = 2, prev_conf + 1

        # ESTADO NEUTRO (0)
        else:
            # 1. NOISE BYPASS (v22.1): Se a saúde for extrema, reentra imediatamente sem pulso QDD
            if last_polar != 0 and health > 85 and bars_neutral < 5:
                r_score, r_conf = last_polar, last_dur + bars_neutral + 1
            
            # 2. FORÇA BRUTA / PAVIO / BREAKOUT (Ignora tudo)
            if r_score == 0 and (is_brute_force or is_breakout_bull or wick_rejection_bull):
                if curr['close'] > ema_trend and not gravity_bull_block: r_score, r_conf = 1, 1
            if r_score == 0 and (is_brute_force or is_breakout_bear or wick_rejection_bear):
                if curr['close'] < ema_trend and not gravity_bear_block: r_score, r_conf = 2, 1
            
            # 3. RE-ENTRADA DE MEMÓRIA (< 60 velas)
            if r_score == 0 and bars_neutral < 60:
                pulse_bull = (qdd_ign == 1 and qdd_ign_p1 == 1)
                pulse_bear = (qdd_ign == 2 and qdd_ign_p1 == 2)
                if last_polar == 1 and (pulse_bull or curr['close'] > ema_trend):
                    r_score, r_conf = 1, last_dur + bars_neutral + 1
                elif last_polar == 2 and (pulse_bear or curr['close'] < ema_trend):
                    r_score, r_conf = 2, last_dur + bars_neutral + 1
            
            # 4. ENTRADA QDD PADRÃO
            if r_score == 0:
                if qdd_ign == 1 and qdd_ign_p1 == 1 and curr['close'] > ema_trend and not gravity_bull_block: r_score, r_conf = 1, 1
                elif qdd_ign == 2 and qdd_ign_p1 == 2 and curr['close'] < ema_trend and not gravity_bear_block: r_score, r_conf = 2, 1
                else: r_score, r_conf = 0, (last_polar * 100000000) + (min(last_dur, 999999) * 100) + min(bars_neutral + 1, 99)

        # MONÓLITO TOTAL (v22.0): Força continuidade visual
        if r_score == prev_score and r_score != 0:
            r_conf = prev_conf + 1

        if debug: return r_score, r_conf, debug_data
        return r_score, r_conf

    @staticmethod
    def calculate_regime_health(df):
        """
        Calcula a saúde da tendência (0-100%).
        CALIBRAÇÃO v21.0: Divisor 2.0 para maior agressividade na Supressão de Hiato.
        """
        if len(df) < 90: return 100
        ema_34 = df['close'].ewm(span=34, adjust=False).mean()
        ema_89 = df['close'].ewm(span=89, adjust=False).mean()
        
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        
        gap = abs(ema_34.iloc[-1] - ema_89.iloc[-1])
        health = min(100, (gap / (atr * 2.0)) * 100)
        return int(health)

    def calculate_rsi(prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_tactical_dots(df, regime_score):
        """
        Gera sinais de tiro Sniper (dots) via C++ QHO-Engine.
        Substitui a lógica estocástica ruidosa por um modelo de poço de potencial de Schrödinger.
        """
        if len(df) < 60: return [0] * len(df)
        
        # O QHO agora ancora o poço de potencial na EMA 34 (Tendência Estrutural)
        ema_34 = df['close'].ewm(span=34, adjust=False).mean()
        
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().fillna(0)
        
        if QDD_AVAILABLE and _QHO_ENGINE_INST is not None:
            try:
                # Converte arrays para numpy C-contiguous float64
                o_arr = np.ascontiguousarray(df['open'].values, dtype=np.float64)
                h_arr = np.ascontiguousarray(df['high'].values, dtype=np.float64)
                l_arr = np.ascontiguousarray(df['low'].values, dtype=np.float64)
                c_arr = np.ascontiguousarray(df['close'].values, dtype=np.float64)
                e34_arr = np.ascontiguousarray(ema_34.values, dtype=np.float64)
                r_arr = np.ascontiguousarray(regime_score, dtype=np.int32)
                atr_arr = np.ascontiguousarray(atr.values, dtype=np.float64)
                
                # Executa o motor quântico em C++
                res = _QHO_ENGINE_INST.scan_quantum_triggers(o_arr, h_arr, l_arr, c_arr, e34_arr, r_arr, atr_arr)
                dots = res['signals'].tolist()
            except Exception as e:
                print(f"Erro QHO Engine: {e}")
                dots = [0] * len(df)
        else:
            dots = [0] * len(df)
            
        # O QHO Engine já retorna 0, 1 (Bull) ou 2 (Bear). 
        # Não precisamos do loop de gradiente antigo, os tiros são únicos (Snipers).
        gradient_dots = [0] * len(dots)
        for i in range(len(dots)):
            if dots[i] == 1:
                gradient_dots[i] = 1 # Verde choque
            elif dots[i] == 2:
                gradient_dots[i] = 2 # Vermelho choque
                
        return gradient_dots
