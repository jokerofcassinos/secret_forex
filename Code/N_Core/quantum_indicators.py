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
    def _get_qdd_regime_with_direction(data_series, timeframe_period=16386, atr=1.0):
        """
        Internal helper v5.4 Stability Patch:
        Elimina oscilação de direção e aplica histerese de fase.
        """
        if not QDD_AVAILABLE or len(data_series) < 64:
            return 0, 0
        
        uv_cutoff = 3
        slope_window = 5
        energy_mult = 0.08
        
        if timeframe_period <= 1: 
            uv_cutoff = 6; slope_window = 30; energy_mult = 0.15
        elif timeframe_period <= 5: 
            uv_cutoff = 5; slope_window = 20; energy_mult = 0.12
        elif timeframe_period <= 15: 
            uv_cutoff = 4; slope_window = 15; energy_mult = 0.10
            
        arr = np.array(data_series, dtype=np.float64)
        try:
            res = _QDD_ENGINE_INST.quantize_regime(arr, uv_cutoff, energy_threshold=atr*energy_mult)
            state = res['regime_state']
            
            direction = 0
            if state >= 1:
                # ANCORAGEM MACRO-ESTRUTURAL (SMA 64)
                # Em vez de olhar a inclinação bruta (que cai em pullbacks),
                # comparamos o preço atual com o preço médio da janela quântica (SMA 64).
                macro_mean = data_series.mean()
                curr_price = data_series.iloc[-1]
                
                # HISTERESE DIRECONAL: Reduzido de 0.1 para 0.02 ATR para ignição instantânea
                slope_threshold = atr * 0.02
                if curr_price > macro_mean + slope_threshold:
                    direction = 1 # Bull
                elif curr_price < macro_mean - slope_threshold:
                    direction = 2 # Bear
                
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

    def advanced_regime_score(self, df_slice, prev_score=0, prev_conf=0, q_math_data=None):
        """
        LÓGICA NEXUS-TQFM v80 (IGNITIVIDADE ABSOLUTA / ZERO LAG):
        1. IGNITIVIDADE ABSOLUTA: Entrada forçada se QDD confirmar + 2 velas de momentum.
        2. EXTREMO LOCAL (40 VELAS): Captura de pivots rápidos em escalas fractais.
        3. FOME DE TENDÊNCIA: Re-entrada imediata na EMA 9 sem threshold de ATR.
        4. MONÓLITO DE FLUXO: Proteção de Tsunami mantida para estabilidade.
        """
        if len(df_slice) < 120: return 0, 0
        
        curr = df_slice.iloc[-1]
        prev1 = df_slice.iloc[-2]
        prev2 = df_slice.iloc[-3]

        # 1. Camadas de Fluxo e Momentum (EMAs)
        if 'ema_fast' in df_slice.columns:
            ema_fast = df_slice['ema_fast'].iloc[-1]; ema_mid = df_slice['ema_mid'].iloc[-1]
            ema_trend = df_slice['ema_trend'].iloc[-1]; ema_macro = df_slice['ema_macro'].iloc[-1]
            ema_gravity = df_slice['ema_gravity'].iloc[-1]
        else:
            ema_fast = df_slice['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            ema_mid = df_slice['close'].ewm(span=21, adjust=False).mean().iloc[-1]
            ema_trend = df_slice['close'].ewm(span=34, adjust=False).mean().iloc[-1]
            ema_macro = df_slice['close'].ewm(span=89, adjust=False).mean().iloc[-1]
            ema_gravity = df_slice['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        
        bull_momentum = (ema_fast > ema_mid); bear_momentum = (ema_fast < ema_mid)
        
        # 2. Dinâmica de Entropia (ATR)
        high_low = df_slice['high'] - df_slice['low']
        high_close = np.abs(df_slice['high'] - df_slice['close'].shift(1))
        low_close = np.abs(df_slice['low'] - df_slice['close'].shift(1))
        atr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean().iloc[-1]

        # 3. DECODE MEMÓRIA (v8.0)
        last_polar_regime = 0
        bars_in_neutral = 0
        if prev_score == 0:
            last_polar_regime = prev_conf // 1000
            bars_in_neutral = prev_conf % 1000
        else:
            last_polar_regime = prev_score
            bars_in_neutral = 0

        # 4. Detecção de Extremos (Cravamento de Topo/Fundo LOCAL v8.0)
        abs_high_40 = df_slice['high'].iloc[-41:-1].max()
        abs_low_40 = df_slice['low'].iloc[-41:-1].min()
        is_abs_top = (curr['high'] >= abs_high_40 - (atr * 0.05))
        is_abs_bottom = (curr['low'] <= abs_low_40 + (atr * 0.05))

        # 5. Soberania e Saúde
        trend_health = self.calculate_regime_health(df_slice)
        is_sovereign = (abs(curr['close'] - ema_trend) > atr * 2.2) or (abs(curr['close'] - ema_macro) > atr * 3.5)
        is_tsunami = (trend_health > 55) and (prev_score != 0 and prev_conf > 12)

        # 6. QDD PURIFICATION
        tf_period = 16386 
        if len(df_slice) >= 2:
            try:
                d_sec = int(df_slice['time'].iloc[-1]) - int(df_slice['time'].iloc[-2])
                if d_sec <= 65: tf_period = 1 
                elif d_sec <= 305: tf_period = 5 
                elif d_sec <= 3605: tf_period = 16385 
            except Exception: pass

        qdd_state, qdd_direction = QuantumIndicators._get_qdd_regime_with_direction(df_slice['close'].iloc[-64:], tf_period, atr)
        is_quantum_event = (qdd_state >= 1)

        # 7. GATILHO DE ACUMULAÇÃO/DISTRIBUIÇÃO (Aceleração Fractal)
        # 2 velas fechando acima da máxima anterior ou abaixo da mínima anterior
        is_accel_bull = (curr['close'] > prev1['high']) and (prev1['close'] > prev2['high'])
        is_accel_bear = (curr['close'] < prev1['low']) and (prev1['close'] < prev2['low'])

        # 8. FILTRO DE MASSA DINÂMICO
        body = abs(curr['close'] - curr['open'])
        is_green = (curr['close'] > curr['open'])
        is_red = (curr['close'] < curr['open'])
        is_atomic = body > (atr * 0.3) 

        # 9. SINGULARIDADE ATÔMICA (Prioridade Máxima)
        # Se estamos no fundo e QDD virou, entramos na primeira vela verde.
        start_atomic_rebound_bull = is_abs_bottom and is_green and (is_atomic or is_accel_bull)
        start_atomic_rebound_bear = is_abs_top and is_red and (is_atomic or is_accel_bear)

        # --- QUANTUM PHASE TRANSITION (QPT) ---
        pti = 0.0; qpt_rec = "STABLE"
        if q_math_data: pti, qpt_rec = self.qpt.evaluate_transition(df_slice, prev_score, q_math_data)

        # 10. MÁQUINA DE ESTADO TQFM v11.0 (IGNITIVIDADE ABSOLUTA)
        
        # 0. OVERRIDES TOTAIS
        if qpt_rec == "IMMEDIATE_PHASE_FLIP" or start_atomic_rebound_bull or start_atomic_rebound_bear:
            if start_atomic_rebound_bull or (qpt_rec == "IMMEDIATE_PHASE_FLIP" and qdd_direction == 1):
                return 1, 0
            if start_atomic_rebound_bear or (qpt_rec == "IMMEDIATE_PHASE_FLIP" and qdd_direction == 2):
                return 2, 0

        if qpt_rec == "MANDATORY_NEUTRAL":
            return 0, (last_polar_regime * 1000) + 1

        pti_exit_threshold = 0.94 if is_tsunami else (0.82 if is_sovereign else 0.55)

        # ESTADO BULL (1)
        if prev_score == 1:
            if is_sovereign:
                if curr['close'] < ema_macro: return 0, 1001
                return 1, min(prev_conf + 1, 50000)
                
            if curr['close'] < (ema_mid if is_tsunami else ema_fast):
                should_exit = (pti > pti_exit_threshold) or (not bull_momentum and curr['close'] < ema_mid)
                if should_exit and qdd_direction == 1: should_exit = False
                if should_exit: return 0, 1001
                
            return 1, min(prev_conf + 1, 50000)

        # ESTADO BEAR (2)
        if prev_score == 2:
            if is_sovereign:
                if curr['close'] > ema_macro: return 0, 2001
                return 2, min(prev_conf + 1, 50000)
                
            if curr['close'] > (ema_mid if is_tsunami else ema_fast):
                should_exit = (pti > pti_exit_threshold) or (not bear_momentum and curr['close'] > ema_mid)
                if should_exit and qdd_direction == 2: should_exit = False
                if should_exit: return 0, 2001

            return 2, min(prev_conf + 1, 50000)

        # ESTADO NEUTRO (0) - FOME DE TENDÊNCIA
        
        # 1. IGNITIVIDADE ABSOLUTA (Fast Entry)
        # Se o QDD validou e o preço cruzou a EMA 9, entramos IMEDIATAMENTE.
        if qdd_direction == 1 and curr['close'] > ema_fast: return 1, 0
        if qdd_direction == 2 and curr['close'] < ema_fast: return 2, 0

        # 2. ACELERAÇÃO POR QUEBRA DE EXTREMO
        if is_accel_bull and qdd_direction == 1: return 1, 0
        if is_accel_bear and qdd_direction == 2: return 2, 0

        # 3. Ignição Estrutural (Noise Gate Residual)
        sig_threshold = atr * 0.3 if (qdd_direction != last_polar_regime) else atr * 0.8
        if (body > sig_threshold) and is_quantum_event and qdd_direction != 0: return qdd_direction, 0
        
        if is_quantum_event:
            if qdd_direction == 1 and curr['close'] > ema_trend: return 1, 0
            if qdd_direction == 2 and curr['close'] < ema_trend: return 2, 0

        return 0, (last_polar_regime * 1000) + min(bars_in_neutral + 1, 999)

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

    def calculate_nexus_score(self, df, density, velocity, regime):
        """
        NEXUS Wyckoff Score (0-100)
        Funde Regime, LBM e Momentum para uma métrica única de dominância.
        """
        try:
            # 1. Componente LBM (40%)
            rho_peak = np.max(density)
            rho_mean = np.mean(density)
            lbm_score = np.clip((rho_peak / (rho_mean + 1e-9)) * 10, 0, 40)
            
            # 2. Componente Momentum (30%)
            mom_score = np.clip(abs(velocity.mean()) * 100, 0, 30)
            
            # 3. Componente de Regime (30%)
            reg_score = 30 if regime != 0 else 10
            
            total_score = lbm_score + mom_score + reg_score
            return int(np.clip(total_score, 0, 100))
        except:
            return 50

    def detect_divergences(self, df, density):
        """
        Detecta divergências entre Preço e Densidade Institucional (LBM).
        """
        if len(df) < 20: return "None"
        
        # Preço fazendo novas máximas vs Densidade caindo
        price_trend = df['close'].iloc[-1] > df['close'].iloc[-10]
        lbm_trend = np.max(density) < 50.0 # Exemplo simplificado
        
        if price_trend and lbm_trend: return "Bearish Div"
        if not price_trend and not lbm_trend: return "Bullish Div"
        return "None"

    def get_market_state(self, df, density, velocity, regime):
        """
        Gera o estado consolidado para o Wyckoff HUD.
        """
        score = self.calculate_nexus_score(df, density, velocity, regime)
        div = self.detect_divergences(df, density)
        
        # Tradução Wyckoff
        state = "NEUTRAL"
        if regime == 1: state = "ACCUMULATION" if score < 70 else "MARK-UP"
        elif regime == 2: state = "DISTRIBUTION" if score < 70 else "MARK-DOWN"
        
        return {
            "score": score,
            "divergence": div,
            "wyckoff_phase": state,
            "strength": round(abs(float(velocity.mean()) * 10), 2)
        }

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
