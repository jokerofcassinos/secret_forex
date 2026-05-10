import numpy as np
import pandas as pd
from Code.N_Core.quantum_phase_transition import QuantumPhaseTransition

def run_qpt_audit():
    print("🌌 NEXUS :: Iniciando Auditoria do Módulo QPT (Phase Transition)...")
    qpt = QuantumPhaseTransition()
    
    # Mock Dataframe
    df = pd.DataFrame({'close': np.linspace(15000, 15100, 100)})
    
    # Cenário 1: Tendência Estável (Ordem Quântica)
    state_stable = {
        "ricci_curvature": 0.5,
        "h_entropy": 0.2,
        "rmt_signal": "PURE_SIGNAL_x4.5",
        "ksi_val": 0.95,
        "is_collapsed": False
    }
    
    pti_1, rec_1 = qpt.evaluate_transition(df, 1, state_stable)
    print(f"\n[CENÁRIO 1: STABLE] PTI: {pti_1:.4f} | Rec: {rec_1}")
    assert pti_1 < 0.4, "Falha: PTI deveria ser baixo em tendência estável."

    # Cenário 2: Exaustão Crítica (Início da Decoerência)
    state_exhaustion = {
        "ricci_curvature": 15.8, # Curvatura explodindo
        "h_entropy": 3.5,       # Desordem subindo
        "rmt_signal": "NOISE_x1.8", # Sinal sendo engolido pelo ruído
        "ksi_val": 0.4,          # Perda de sincronia
        "is_collapsed": False
    }
    
    pti_2, rec_2 = qpt.evaluate_transition(df, 1, state_exhaustion)
    print(f"[CENÁRIO 2: EXHAUSTION] PTI: {pti_2:.4f} | Rec: {rec_2}")
    assert pti_2 > 0.7, "Falha: PTI deveria detectar instabilidade crítica."

    # Cenário 3: Colapso Topológico (Imediato)
    state_collapse = {
        "ricci_curvature": 25.0,
        "h_entropy": 6.0,
        "rmt_signal": "NOISE_x0.9",
        "ksi_val": 0.1,
        "is_collapsed": True
    }
    
    pti_3, rec_3 = qpt.evaluate_transition(df, 1, state_collapse)
    print(f"[CENÁRIO 3: COLLAPSE] PTI: {pti_3:.4f} | Rec: {rec_3}")
    assert pti_3 > 0.9, "Falha: PTI deveria estar em nível de colapso imediato."

    print("\n✅ AUDITORIA CONCLUÍDA. O Módulo QPT está calibrado para eliminar o lag cronodinâmico.")

if __name__ == "__main__":
    run_qpt_audit()
