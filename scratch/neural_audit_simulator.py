import os
import sys
import numpy as np
import time
import pandas as pd

# [NEXUS SCRATCH] NEURAL AUDIT SIMULATOR v1.0
# Simula um colapso topológico e testa a resposta da física do Aethelgard.

root = os.getcwd()
sys.path.append(root)

try:
    from q_math_node import QMathNode
    print("NEXUS ONLINE: Simulador de Catástrofe Quântica Ativado.")
except ImportError:
    print("ERRO: QMathNode não encontrado.")
    sys.exit()

def simulate_flash_crash():
    node = QMathNode()
    
    # 1. Fase de Estabilidade (Mercado Lateral)
    print("\n[STRESS TEST] FASE 1: Estabilidade (Ruído Gaussiano)")
    df = pd.DataFrame({
        'open': np.random.normal(80000, 10, 100),
        'high': np.random.normal(80010, 10, 100),
        'low': np.random.normal(79990, 10, 100),
        'close': np.random.normal(80000, 10, 100),
        'tick_volume': np.random.normal(500, 50, 100)
    })
    
    node.calculate_quantum_state(df, 1) # Regime BULL
    print(">> Estado: Estabilizado. Telemetria gerada.")

    # 2. Fase de Colapso (Flash Crash Sintético)
    print("\n[STRESS TEST] FASE 2: Colapso Topológico (Derivada Extrema)")
    # Simula queda de 10% em 5 barras com volume 10x maior
    crash_data = {
        'open': [80000, 78000, 76000, 74000, 72000],
        'high': [80100, 78100, 76100, 74100, 72100],
        'low': [77900, 75900, 73900, 71900, 69900],
        'close': [78000, 76000, 74000, 72000, 70000],
        'tick_volume': [5000, 8000, 12000, 15000, 20000]
    }
    df_crash = pd.concat([df, pd.DataFrame(crash_data)], ignore_index=True)
    
    start_t = time.perf_counter()
    res = node.calculate_quantum_state(df_crash, 2) # Regime BEAR
    end_t = time.perf_counter()
    
    print(f">> RESPOSTA NEURAL EM: {(end_t - start_t)*1000:.2f}ms")
    print(f">> RICCI CURVATURE: {res.get('ricci_curvature', 0):.4f} sigma")
    print(f">> ENTROPIA BH: {res.get('h_entropy', 0):.4f}")
    
    if res.get('ricci_curvature', 0) > 0.8:
        print("!!! ALERTA DE SINGULARIDADE DISPARADO: SUCESSO !!!")
    else:
        print("??? FALHA: A física não detectou o colapso estrutural.")

if __name__ == "__main__":
    simulate_flash_crash()
