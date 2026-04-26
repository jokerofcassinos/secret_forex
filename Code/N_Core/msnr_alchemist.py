import numpy as np
import pandas as pd

class MSNRAlchemist:
    """
    MSNR-Alchemist (Market Structure Noise Reduction)
    Agente responsável por transmutar dados brutos em zonas de Ressonância Quântica.
    Funde conceitos de SMC, Liquidez Institucional e Estrutura de Fluxo.
    """
    
    def __init__(self, fibo_levels=[0.5, 0.618, 0.786], bb_period=20, bb_std=2.0):
        self.fibo_levels = fibo_levels
        self.bb_period = bb_period
        self.bb_std = bb_std

    def calculate_dealing_range(self, df, lookback=100):
        """
        Define o range de negociação atual (Topos e Fundos Reais).
        Retorna o 'Equilibrium' (50%) e as zonas Premium/Discount.
        """
        high_range = df['high'].iloc[-lookback:].max()
        low_range = df['low'].iloc[-lookback:].min()
        diff = high_range - low_range
        
        equilibrium = low_range + (diff * 0.5)
        premium_zone = high_range - (diff * 0.214) # Acima de 78.6%
        discount_zone = low_range + (diff * 0.214)  # Abaixo de 21.4%
        
        return {
            'high': high_range,
            'low': low_range,
            'equilibrium': equilibrium,
            'premium': premium_zone,
            'discount': discount_zone
        }

    def detect_structure_change(self, df, lookback=50):
        """
        Detecta BOS (Break of Structure) e CHoCH (Change of Character).
        BOS: Continuação de tendência (Fechamento além do topo/fundo anterior).
        CHoCH: Reversão (Fechamento além do pivô contrário).
        """
        if len(df) < lookback + 5: return None
        
        # Encontrar últimos pivôs (Highs e Lows significativos)
        # Usamos uma janela de 5 velas para definir um pivô
        pivots_high = []
        pivots_low = []
        
        for i in range(len(df) - lookback, len(df) - 2):
            if df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i+1]:
                pivots_high.append(df['high'].iloc[i])
            if df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i+1]:
                pivots_low.append(df['low'].iloc[i])

        if not pivots_high or not pivots_low: return None

        last_high = pivots_high[-1]
        last_low = pivots_low[-1]
        curr_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]

        # Lógica de CHoCH (Change of Character)
        choch_bull = (prev_close <= last_high < curr_close)
        choch_bear = (prev_close >= last_low > curr_close)

        return "CHOCH_BULL" if choch_bull else "CHOCH_BEAR" if choch_bear else None

    def detect_liquidity_sweeps(self, df, lookback=50):
        """
        Detecta varreduras de liquidez institucional (Stop Hunts).
        Verifica se o preço ultrapassou um extremo de longo prazo e retornou.
        """
        curr = df.iloc[-1]
        # Extremos de longo prazo (excluindo os últimos 5 candles para evitar ruído)
        major_high = df['high'].iloc[-lookback:-5].max()
        major_low = df['low'].iloc[-lookback:-5].min()
        
        body = abs(curr['close'] - curr['open'])
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        
        # Sweep: Rompeu a máxima/mínima histórica mas o fechamento voltou para dentro
        if curr['high'] > major_high and curr['close'] < major_high:
            if upper_wick > body: return "BSL_SWEEP" # Buy Side Liquidity taken
            
        if curr['low'] < major_low and curr['close'] > major_low:
            if lower_wick > body: return "SSL_SWEEP" # Sell Side Liquidity taken
            
        return None

    def detect_fvgs(self, df, lookback=30):
        fvgs = []
        for i in range(len(df) - 2, len(df) - lookback, -1):
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                fvgs.append({'type': 'BULL_FVG', 'top': df['low'].iloc[i], 'bottom': df['high'].iloc[i-2], 'age': len(df)-i})
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                fvgs.append({'type': 'BEAR_FVG', 'top': df['low'].iloc[i-2], 'bottom': df['high'].iloc[i], 'age': len(df)-i})
        return fvgs

    def validate_sovereign_signal(self, df, regime, is_genesis=False):
        """
        Valida se o sinal é SOBERANO (SRF v85).
        Protocolo de Ressonância Estrutural: Foco em Sweeps Locais e Expansão.
        """
        dr = self.calculate_dealing_range(df)
        curr = df.iloc[-1]
        curr_price = curr['close']
        
        # 1. Parâmetros de Volatilidade e Força
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        body = abs(curr['close'] - curr['open'])
        
        # Força v85 (Adaptada para M1)
        is_blast = body > (atr * 1.2)
        is_atomic = body > (atr * 1.0)

        # 2. GATILHOS DE LIQUIDEZ LOCAL (Micro-Sweeps 20 candles)
        # Captura pivôs de tendência que não são recordes de 2h
        local_high = df['high'].iloc[-20:-1].max()
        local_low = df['low'].iloc[-20:-1].min()
        
        is_local_sweep_top = curr['high'] >= local_high and curr['close'] < local_high
        is_local_sweep_bottom = curr['low'] <= local_low and curr['close'] > local_low

        # 3. PROTOCOLO SRF v85 (Gênese Sniper)
        if is_genesis:
            # PRIORIDADE 1: BLAST INSTITUCIONAL (Captura o Início dos Gigantes)
            if is_blast: return True
            
            # PRIORIDADE 2: MICRO-SWEEP (Captura o 'Bear Giant' em topo descendente)
            if regime == 1 and is_local_sweep_bottom: return True
            if regime == 2 and is_local_sweep_top: return True
            
            # CASO C: GÊNESE COMUM -> EXIGE EXTREMO DE VALOR (Proteção contra Ruído)
            if regime == 1 and curr_price < (dr['low'] + (dr['high'] - dr['low']) * 0.2): return True
            if regime == 2 and curr_price > (dr['high'] - (dr['high'] - dr['low']) * 0.2): return True
            
            return False

        # 4. FILTRO DE QUARENTENA (Para Re-entradas)
        box_size = dr['high'] - dr['low']
        # Só permite re-entrada em boxes com amplitude real (> 3.5x ATR)
        if box_size < (atr * 3.5): return False

        # 5. LÓGICA DE RE-ENTRADA (Apenas em Zonas de Valor Profundo)
        if regime == 1: # BULL
            if curr_price < (dr['low'] + box_size * 0.25) and is_atomic: return True
            
        if regime == 2: # BEAR
            if curr_price > (dr['high'] - box_size * 0.25) and is_atomic: return True
            
        return False






















    def find_structural_targets(self, df, regime, lookback=200):
        """
        Busca alvos de Liquidez Externa v67 (External Range Liquidity).
        Implementa Expansão Soberana para movimentos de alto momentum.
        """
        curr_price = df['close'].iloc[-1]
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
        is_super_atomic = body > (atr * 1.5)

        # Mapeia os extremos do fractal macro (Lookback maior para o Bear Gigante)
        major_high = df['high'].iloc[-lookback:].max()
        major_low = df['low'].iloc[-lookback:].min()
        range_size = major_high - major_low

        if regime == 1: # BULL
            # Se for Super Atômico, mira na expansão do range
            if is_super_atomic:
                target = major_high + (range_size * 0.618)
            else:
                target = major_high
            
            # Stop Loss Dinâmico (Trailing Structural)
            stop = df['low'].iloc[-40:].min() - (atr * 0.2)
            if stop >= curr_price: stop = curr_price - (atr * 3.0)

        else: # BEAR
            if is_super_atomic:
                target = major_low - (range_size * 0.618)
            else:
                target = major_low

            stop = df['high'].iloc[-40:].max() + (atr * 0.2)
            if stop <= curr_price: stop = curr_price + (atr * 3.0)

        return target, stop



if __name__ == "__main__":
    print("MSNR-Alchemist: Sistema de Alquimia de Mercado Inicializado.")
