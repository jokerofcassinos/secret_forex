import numpy as np
import pandas as pd

class FotismenoiAgent:
    def __init__(self):
        self.pec_level = 0

    def decode_resonance(self, df_zone, regime):
        """
        LÓGICA FOTIS M1 (V23):
        Focada em validar o início imediato e a sustentação.
        """
        if len(df_zone) < 5: return None
        
        prices = df_zone['close']
        volumes = df_zone['tick_volume']
        pec = (prices * volumes).sum() / (volumes.sum() + 1e-9)
        self.pec_level = pec
        
        curr_p = prices.iloc[-1]
        
        if regime == "BULL":
            if curr_p >= pec: # Preço acima da massa
                return {"signal": "ENGATILHAR", "reason": "Luz Ativa", "level": pec}
        if regime == "BEAR":
            if curr_p <= pec: # Preço abaixo da massa
                return {"signal": "ENGATILHAR", "reason": "Sombra Ativa", "level": pec}

        return {"signal": "AGUARDAR", "reason": "Neutralidade"}
