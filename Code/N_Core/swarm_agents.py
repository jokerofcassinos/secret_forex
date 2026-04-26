import numpy as np
import pandas as pd
from scipy.stats import kurtosis

class PythonisAgent:
    """Especialista em Densidade de Ticks (ADT) - Rigor Master"""
    def __init__(self):
        self.id = "PYTHONIS_001"

    def analyze_density(self, df_tick_window, df_context):
        if len(df_tick_window) < 3: return 0
        
        # Só valida se o fechamento for 'cheio' (Corpo > 70% do tamanho total)
        last = df_tick_window.iloc[-1]
        total_range = abs(last['high'] - last['low']) + 1e-9
        body = abs(last['close'] - last['open'])
        if (body / total_range) < 0.6: return 0 # Veta candles de indecisão (pavios longos)

        price_range = abs(df_tick_window['close'].max() - df_tick_window['close'].min()) + 1e-9
        current_vol = df_tick_window['tick_volume'].sum()
        current_density = current_vol / price_range
        
        ctx_range = abs(df_context['close'].max() - df_context['close'].min()) + 1e-9
        ctx_vol = df_context['tick_volume'].sum()
        avg_density = ctx_vol / ctx_range
            
        return current_density / (avg_density + 1e-9)

class KyvernitisAgent:
    """O Governador de Risco - Filtro de Barreira Estrutural"""
    def __init__(self):
        self.id = "KYVERNITIS_001"

    def validate_structural_zone(self, price, df_long):
        """Só permite operar se o preço não estiver em zona de exaustão macro."""
        if len(df_long) < 100: return False
        
        high_100 = df_long['high'].tail(100).max()
        low_100 = df_long['low'].tail(100).min()
        range_100 = high_100 - low_100 + 1e-9
        
        # Filtro de Compra: Preço deve estar abaixo dos 60% do range (Desconto)
        # Filtro de Venda: Preço deve estar acima dos 40% do range (Prêmio)
        rel_pos = (price - low_100) / range_100
        
        return rel_pos # Retorna a posição relativa para o orquestrador
