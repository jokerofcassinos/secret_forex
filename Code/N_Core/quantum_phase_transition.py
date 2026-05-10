import numpy as np
import pandas as pd
from typing import Tuple, Dict

class QuantumPhaseTransition:
    """
    NEXUS QPT :: Phase Transition Quantum Module (v1.1)
    
    Finalidade: Eliminar o lag de regime (EMA 34/89) detectando o Ponto Crítico (Criticality)
    através da Teoria Quântica de Fluidos de Mercado (TQFM).
    """
    
    def __init__(self):
        self.pti_threshold = 0.65  # Threshold de Criticalidade Reduzido (Mais sensível)
        self.history_pti = []
        self.prev_ricci = 0.0
        
    def calculate_pti(self, 
                      ricci_curvature: float, 
                      h_entropy: float, 
                      power_ratio: float, 
                      ksi_val: float,
                      is_collapsed: bool) -> float:
        """
        Calcula o Phase Transition Intensity (PTI).
        Normaliza e funde os tensores de instabilidade.
        """
        # 1. Ricci Curvature (Aumentada sensibilidade para deformações rápidas)
        ricci_norm = np.tanh(abs(ricci_curvature) / 5.0) # Divisor menor = mais sensível
        
        # 2. Entropy Divergence (Holographic)
        entropy_norm = np.tanh(h_entropy / 3.0)
        
        # 3. RMT Decoherence (SVD Proxy)
        # Mais agressivo na decoerência
        svd_decay = 1.0 - np.tanh(max(0, power_ratio - 0.5) / 2.0)
        
        # 4. KSI Desynchronization
        sync_loss = 1.0 - ksi_val
        
        # Aceleração de Ricci (Singularidade de Impulso)
        ricci_accel = max(0, abs(ricci_curvature) - abs(self.prev_ricci))
        accel_norm = np.tanh(ricci_accel / 2.0)
        self.prev_ricci = ricci_curvature
        
        # Pesos da ASI (Prioridade: Geometria + Aceleração > Espectro > Entropia)
        weights = np.array([0.45, 0.25, 0.20, 0.10])
        # Funde Ricci com sua própria aceleração
        geom_factor = max(ricci_norm, accel_norm)
        
        metrics = np.array([geom_factor, svd_decay, entropy_norm, sync_loss])
        
        pti_score = np.dot(weights, metrics)
        
        # Bônus de Colapso Topológico (Aumentado para 0.4)
        if is_collapsed:
            pti_score = min(1.0, pti_score + 0.4)
            
        return float(pti_score)

    def evaluate_transition(self, 
                            df_slice: pd.DataFrame, 
                            current_regime: int,
                            q_math_data: Dict) -> Tuple[float, str]:
        """
        Avalia se deve ocorrer uma transição de fase imediata.
        Normaliza regimes (Ghost/Exhaustion) para compatibilidade v23.1.
        """
        ricci = q_math_data.get("ricci_curvature", 0.0)
        entropy = q_math_data.get("h_entropy", 0.0)
        # Saneamento de RMT Signal
        rmt_sig = str(q_math_data.get("rmt_signal", "NOISE_x1.0"))
        power_ratio = 1.0
        if 'x' in rmt_sig:
            try: power_ratio = float(rmt_sig.split('x')[-1])
            except: pass
            
        ksi = q_math_data.get("ksi_val", 0.0)
        is_collapsed = q_math_data.get("is_collapsed", False)
        
        pti = self.calculate_pti(ricci, entropy, power_ratio, ksi, is_collapsed)
        self.history_pti.append(pti)
        if len(self.history_pti) > 100: self.history_pti.pop(0)
        
        # Normalização de Regime (v23.1)
        norm_r = current_regime % 10 if current_regime > 10 else current_regime

        # Lógica de Recomendação (Early Warning)
        recommendation = "STABLE"
        
        if len(df_slice) > 20:
            price_trend = df_slice['close'].iloc[-1] > df_slice['close'].iloc[-10]
            if norm_r == 1 and price_trend and pti > 0.70:
                recommendation = "BULL_EXHAUSTION_WARNING"
            elif norm_r == 2 and not price_trend and pti > 0.70:
                recommendation = "BEAR_EXHAUSTION_WARNING"

        # Detecção de Ponto Crítico - SOBRESCREVE EXAUSTÃO SE FOR CRÍTICO
        if pti > self.pti_threshold:
            if pti > 0.90:
                recommendation = "IMMEDIATE_PHASE_FLIP"
            elif pti > 0.80:
                recommendation = "MANDATORY_NEUTRAL"
            elif recommendation == "STABLE": # Se não foi exaustão, mas passou do threshold
                recommendation = "CRITICAL_INSTABILITY"

        return pti, recommendation

if __name__ == "__main__":
    print("NEXUS QPT Module Loaded. Protocol ASI-5 Ready.")
