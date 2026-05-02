import pandas as pd
import numpy as np
from Code.N_Core.quantum_indicators import QuantumIndicators

def test_integration():
    print("Iniciando Teste de Integração Nexus v5.0 (RG-QDD)...")
    
    # Cria dados sintéticos de teste
    dates = pd.date_range(start='2026-01-01', periods=200, freq='2h')
    data = {
        'open': np.linspace(15000, 15500, 200) + np.random.normal(0, 5, 200),
        'high': np.linspace(15010, 15510, 200) + np.random.normal(0, 5, 200),
        'low': np.linspace(14990, 15490, 200) + np.random.normal(0, 5, 200),
        'close': np.linspace(15005, 15505, 200) + np.random.normal(0, 5, 200),
    }
    # Injeta Salto Quântico (Injeção de Liquidez)
    data['close'][-10:] += 500
    data['high'][-10:] += 500
    data['open'][-10:] += 450
    
    df = pd.DataFrame(data, index=dates)
    
    # Testa o score de regime com o novo Gate QDD
    score, conf = QuantumIndicators.advanced_regime_score(df, prev_score=0, prev_conf=0)
    
    print(f"\n[RESULTADO]")
    print(f" > Regime Detectado: {score} (1=Bull, 2=Bear, 0=Neutral)")
    print(f" > Confiança: {conf}")
    
    if score != 0:
        print("✅ QDD Gate permitiu a detecção de regime direcional.")
    else:
        print("ℹ️ QDD Gate filtrou o movimento como ruído térmico (E0).")

if __name__ == "__main__":
    test_integration()
