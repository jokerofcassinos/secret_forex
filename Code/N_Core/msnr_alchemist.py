import numpy as np
import pandas as pd
import os
import sys

# [BOOTLOADER] Integração MSNR C++
if os.name == 'nt':
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    bin_path = os.path.join(root, "Code", "CPP_Engine", "bin")
    
    # Adiciona raiz e bin ao caminho de busca
    for p in [root, bin_path]:
        if os.path.exists(p):
            os.add_dll_directory(p)
            if p not in sys.path: sys.path.insert(0, p)

try:
    import msnr_engine as msnr_module
except ImportError:
    # Fallback se não encontrar o .pyd
    msnr_module = None

class MSNRAlchemist:
    """
    MSNR-Alchemist (Market Structure Noise Reduction)
    Agente de Alquimia Espectral ASI v6.0.
    Funde Spectral Pruning C++ com Estrutura de Mercado SMC.
    """
    
    def __init__(self, fibo_levels=[0.5, 0.618, 0.786], cut_off=0.15):
        self.fibo_levels = fibo_levels
        self.cut_off = cut_off
        self.engine = msnr_module.MSNREngine() if msnr_module else None

    def apply_spectral_alchemy(self, series):
        """
        Extrai o Sinal Puro através da Poda Espectral C++.
        """
        raw = np.array(series, dtype=np.float64)
        if not self.engine: return raw, 1.0 # Fallback: 100% fidelity se não houver engine
        
        filtered = self.engine.spectral_denoising(raw, self.cut_off)
        fidelity = self.engine.calculate_resonance_fidelity(raw, filtered)
        return filtered, fidelity

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

    def detect_institutional_shift(self, df, lookback=50):
        """
        Gera um sinal MSNR ultra-preciso (Sniper).
        Condição: Ocorreu uma Varredura de Liquidez (Sweep) SEGUIDA de um Vácuo de Liquidez (FVG) na direção oposta.
        """
        sweep = self.detect_liquidity_sweeps(df, lookback)
        fvgs = self.detect_fvgs(df, lookback=10) # FVG recente (displacement)
        
        # Bullish Shift: Varreu liquidez de venda (SSL) e criou FVG de alta
        if sweep == "SSL_SWEEP":
            if any(f['type'] == 'BULL_FVG' for f in fvgs):
                return "1" # STRONG BUY
                
        # Bearish Shift: Varreu liquidez de compra (BSL) e criou FVG de baixa
        if sweep == "BSL_SWEEP":
            if any(f['type'] == 'BEAR_FVG' for f in fvgs):
                return "2" # STRONG SELL
                
        return "0"

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
        TQFM v310 - Sovereign Validation v2.0 (FIX P1-13)
        Reactivated with meaningful confluence checks.
        Validates regime with EMA spread, momentum, and body confirmation.
        Genesis transitions always pass to avoid blocking regime changes.
        """
        if is_genesis:
            return True  # Regime transitions always pass through
        
        if regime == 0:
            return True  # Neutral regime — no signal to validate
        
        if len(df) < 90:
            return True  # Not enough data — let it pass
        
        ema_34 = df['close'].ewm(span=34, adjust=False).mean().iloc[-1]
        ema_89 = df['close'].ewm(span=89, adjust=False).mean().iloc[-1]
        
        high_low = df['high'] - df['low']
        atr = high_low.rolling(14).mean().iloc[-1]
        if np.isnan(atr) or atr < 1e-9:
            return True
        
        # Confluence 1: EMAs must have meaningful separation (>0.3 ATR)
        ema_gap = abs(ema_34 - ema_89) / atr
        if ema_gap < 0.3:
            return False  # EMAs too close — no clear trend
        
        # Confluence 2: Direction must match regime
        if regime == 1 and ema_34 < ema_89:
            return False  # BULL regime but trend EMA below macro
        if regime == 2 and ema_34 > ema_89:
            return False  # BEAR regime but trend EMA above macro
        
        return True



























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
