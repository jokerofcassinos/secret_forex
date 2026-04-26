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
        Valida se o sinal é SOBERANO (PSA v90).
        Master Operability Lock: Sniper apenas em Mercados com Amplitude.
        """
        # 1. Parâmetros de Contexto (2 horas)
        high_120 = df['high'].iloc[-120:].max()
        low_120 = df['low'].iloc[-120:].min()
        total_range = high_120 - low_120
        
        curr = df.iloc[-1]
        curr_price = curr['close']
        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        body = abs(curr['close'] - curr['open'])
        
        # 2. MASTER OPERABILITY LOCK (MOL)
        # Se o mercado está lateralizado (range < 8x ATR), o RR é lixo. Hibernação.
        is_market_alive = total_range >= (atr * 8.0)
        
        # Níveis de Força
        is_god_blast = body > (atr * 2.2) # Quebra de Hibernação
        is_blast = body > (atr * 1.3)
        is_atomic = body > (atr * 1.0)

        # 3. SINGULARIDADES
        is_absolute_ext = curr['low'] <= low_120 + (atr * 0.1) or curr['high'] >= high_120 - (atr * 0.1)

        # 4. PROTOCOLO PSA v90 (Soberania de Contexto)
        if is_genesis:
            # Caso A: God Blast (Sempre válido - rompe a hibernação)
            if is_god_blast: return True
            
            # Se o mercado estiver 'Morto', bloqueia tudo o resto
            if not is_market_alive: return False
            
            # PRIORIDADE 1: EXTREMO ABSOLUTO (Fundo/Topo Real em Mercado Ativo)
            if is_absolute_ext: return True
            
            # PRIORIDADE 2: BLAST INSTITUCIONAL (Captura o início dos Gigantes)
            if is_blast: return True
            
            return False

        # 5. FILTRO DE MAGNITUDE PARA RE-ENTRADAS
        # Só permite novas ordens se o box já provou ser um monstro de magnitude.
        if total_range < (atr * 5.0): return False

        # 6. LÓGICA DE RE-ENTRADA (Extremos de Boxes Maduros)
        if regime == 1: # BULL
            if curr_price < (low_120 + total_range * 0.2) and is_atomic: return True
        if regime == 2: # BEAR
            if curr_price > (high_120 - total_range * 0.2) and is_atomic: return True
            
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
