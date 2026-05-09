import os
import sys
import numpy as np
import pandas as pd

# Configuração de Caminhos para DLLs
root_path = os.getcwd()
if sys.platform == 'win32':
    if os.path.exists(r"D:\msys64\mingw64\bin"):
        os.add_dll_directory(r"D:\msys64\mingw64\bin")
    os.add_dll_directory(root_path)
sys.path.append(root_path)

try:
    import qho_engine
except ImportError:
    print("FAIL: qho_engine não encontrado. Certifique-se de compilar primeiro.")

class QuantumOscillatorNode:
    """
    Orquestrador do Oscilador Harmônico Quântico (QHO).
    Mapeia o desvio do preço (Z-Score) em níveis de energia estacionários (n).
    Detecta estados de sobre-excitação (Bolha/Exaustão) via quantização.
    """
    def __init__(self):
        self.engine = qho_engine.QHOEngine()
        self.fair_value_window = 20
        
    def calculate_quantum_state(self, df):
        """
        Calcula o IFV (Fair Value), o Z-Score e o Nível de Energia (n).
        """
        if len(df) < self.fair_value_window:
            return {"n": 0, "stability": 1.0, "ifv": df['close'].iloc[-1]}
            
        # Calcula Institutional Fair Value (IFV) via VWAP ou Média Ponderada
        recent = df.tail(self.fair_value_window)
        ifv = recent['close'].mean()
        current_price = df['close'].iloc[-1]
        local_std = df['close'].tail(10).std() + 1e-9
        z_score = ((current_price - ifv) / local_std) * 3.0 # Amplificação Tática
        
        # Cálculo C++ dos Estados Estacionários
        n_level = self.engine.estimate_energy_level(z_score)
        stability = self.engine.calculate_stability_score(z_score)
        
        # Onda de Probabilidade (psi_n)
        wave_val = self.engine.calculate_wavefunction(n_level, z_score)
        
        # Shells Visuais (Cascas de Energia em Preço) - Escala Tática (0.25 sigma por nível)
        std_dev = df['close'].tail(self.fair_value_window).std() + 1e-9
        shells = [ifv + (i * 0.25 * std_dev) for i in range(-5, 6) if i != 0]
        
        return {
            "n": n_level,
            "stability": stability,
            "ifv": ifv,
            "z_score": z_score,
            "wave_prob": wave_val**2,
            "status": self.get_energy_status(n_level, z_score),
            "shells": shells
        }

    def get_energy_status(self, n, z):
        if n == 0: return "GROUND_STATE"
        if n <= 2: return "STABLE_EXCITATION"
        if n <= 5: return "HIGH_ENERGY_ALERT"
        return "CRITICAL_EXHAUSTION" if z > 0 else "CRITICAL_DEPRESSION"

if __name__ == "__main__":
    # Teste de Sanidade
    node = QuantumOscillatorNode()
    fake_df = pd.DataFrame({'close': np.random.normal(15000, 50, 300)})
    state = node.calculate_quantum_state(fake_df)
    print(f"DEBUG QHO State: n={state['n']}, Stability={state['stability']:.4f}, Status={state['status']}")
