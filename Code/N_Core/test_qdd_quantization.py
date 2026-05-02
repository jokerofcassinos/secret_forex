import numpy as np
import sys
import os

# Adiciona o caminho das extensões C++
sys.path.append(os.path.join(os.getcwd(), 'Code', 'CPP_Engine'))

# Adiciona o diretório do MinGW para carregar as DLLs de dependência (libstdc++, libgcc, etc)
if sys.platform == 'win32':
    os.add_dll_directory(r"D:\msys64\mingw64\bin")

try:
    import qdd_engine
    print("✅ Módulo QDD_Engine importado com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar QDD_Engine: {e}")
    sys.exit(1)

def run_test():
    # Inicializa o motor: dim=1, hbar=1.0, gamma=0.05
    engine = qdd_engine.QDDEngine(1, 1.0, 0.05)
    
    print(f"\n[CONFIG] Gamma (Dissipação): {engine.get_gamma()}")
    
    # 1. Simulação de Ruído Térmico (Estado Fundamental E0)
    noise_data = np.random.normal(0, 0.1, 1024).astype(np.float64)
    res_noise = engine.quantize_regime(noise_data, uv_cutoff=3, energy_threshold=0.5)
    print(f"\n[TESTE 1 - RUÍDO]")
    print(f" > Regime: E{res_noise['regime_state']} ({'Noise' if res_noise['regime_state']==0 else 'Erro'})")
    print(f" > Energia: {res_noise['energy_level']:.6f}")
    print(f" > Coerência: {res_noise['coherence']:.4f}")

    # 2. Simulação de Fluxo Laminar (Estado Excitado E1)
    # Criamos uma tendência com inércia (momento)
    t = np.linspace(0, 10, 1024)
    laminar_data = (np.sin(t) + np.random.normal(0, 0.02, 1024)).astype(np.float64)
    res_laminar = engine.quantize_regime(laminar_data, uv_cutoff=3, energy_threshold=0.005)
    print(f"\n[TESTE 2 - LAMINAR]")
    print(f" > Regime: E{res_laminar['regime_state']} ({'Laminar' if res_laminar['regime_state']==1 else 'Falha'})")
    print(f" > Energia: {res_laminar['energy_level']:.6f}")
    print(f" > Coerência: {res_laminar['coherence']:.4f}")

    # 3. Simulação de Choque de Alta Energia (Estado En)
    shock_data = np.zeros(1024)
    shock_data[500:520] = np.linspace(0, 5, 20) # Salto violento
    res_shock = engine.quantize_regime(shock_data.astype(np.float64), uv_cutoff=1, energy_threshold=0.1)
    print(f"\n[TESTE 3 - SHOCK]")
    print(f" > Regime: E{res_shock['regime_state']} ({'Shock' if res_shock['regime_state']>=2 else 'Falha'})")
    print(f" > Energia: {res_shock['energy_level']:.6f}")

if __name__ == "__main__":
    run_test()
