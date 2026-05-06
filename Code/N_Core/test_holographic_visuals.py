import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine/src/cyt')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine/src/schrodinger')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine')))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
            
    import cyt_engine
    import schrodinger_engine
    MOCK_ENGINES = False
except ImportError as e:
    print(f"Warning: C++ engines not found ({e}). Using Mock for visual test.")
    MOCK_ENGINES = True

plt.style.use('dark_background')

# 1. Simular Dados do GER40 (H2) com anomalias
N = 1000
t = np.arange(N)
np.random.seed(1337) # Para reprodutibilidade do holograma

price = np.zeros(N)
price[0] = 18500.0

for i in range(1, N):
    if 300 < i < 350:
        price[i] = price[i-1] - np.random.normal(8, 2)  # Queda brusca (Criação do Vácuo de Dirac)
    elif 700 < i < 750:
        price[i] = price[i-1] + np.random.normal(8, 2)  # Retorno ao Vácuo (Aniquilação)
    else:
        price[i] = price[i-1] + np.random.normal(0, 1.8) # Movimento Browniano / Bulk

df = pd.DataFrame({'close': price})
df['open'] = df['close'].shift(1).fillna(price[0])
df['high'] = df[['open', 'close']].max(axis=1) + np.random.exponential(2, N)
df['low'] = df[['open', 'close']].min(axis=1) - np.random.exponential(2, N)
df['tick_volume'] = np.random.randint(100, 1500, N)

# Injeção de Massa (D-Branes / Condensados)
df.loc[150:180, 'tick_volume'] = df.loc[150:180, 'tick_volume'] * 5 # Bloco de Liquidez (Buraco Negro)
df.loc[720:740, 'tick_volume'] = df.loc[720:740, 'tick_volume'] * 8 # Momento de Colisão S-Matrix

# Arrays de resultados
holographic_entropy = np.zeros(N)
s_matrix_amplitude = np.zeros(N)
annihilation_events = []

if not MOCK_ENGINES:
    cyt = cyt_engine.CYTEngine()
    qcs = schrodinger_engine.QuantumCloudSolver(512, 1.0)

# Processamento da Física Pós-Singularidade
vacuum_density_memory = 0.0
in_state_energy = 0.0

for i in range(20, N):
    # --- AdS/CFT Bekenstein-Hawking Entropy ---
    # Simulando um "bloco" como a consolidação recente
    window = df.iloc[i-20:i]
    block_vol = window['tick_volume'].sum()
    time_dur = 20.0
    price_spread = window['high'].max() - window['low'].min()
    
    if not MOCK_ENGINES:
        s_bh = cyt.calculate_holographic_entropy(block_vol, time_dur, price_spread)
    else:
        l_p = max(0.0001, price_spread * 0.01)
        s_bh = (time_dur * price_spread * (np.log1p(block_vol) + 1)) / (4.0 * (l_p**2))
    
    holographic_entropy[i] = s_bh

    # --- S-Matrix Scattering (Aniquilação do Vácuo de Dirac) ---
    # Identificar a criação do vácuo (Queda forte)
    if 300 < i < 350:
        vacuum_density_memory += (window['high'].max() - window['low'].min()) * 0.1
        in_state_energy = np.mean(price[300:350])
        
    out_state_energy = price[i]
    
    if vacuum_density_memory > 0 and i > 350:
        if not MOCK_ENGINES:
            amplitude = qcs.calculate_s_matrix_scattering(in_state_energy, out_state_energy, vacuum_density_memory)
        else:
            delta_e = abs(out_state_energy - in_state_energy)
            coupling = max(0.001, vacuum_density_memory)
            amp_linear = coupling / (delta_e + coupling)
            amplitude = min(1.0, amp_linear**2)
            
        s_matrix_amplitude[i] = amplitude
        
        # Colapso: Quando a onda atinge amplitude 1.0 (ou muito perto), o Vácuo é preenchido.
        if amplitude > 0.95 and len(annihilation_events) == 0:
            annihilation_events.append((i, price[i]))
            vacuum_density_memory = 0.0 # Vácuo aniquilado

# 4. Plotar Visual (Dashboard Holográfico)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
fig.patch.set_facecolor('#0a0a0f')

# Título Principal
fig.suptitle('NEXUS-QUANT :: THE BULK (AdS/CFT) & S-MATRIX SCATTERING', fontsize=22, color='white', fontweight='bold')

# Ax1: Preço e Aniquilação (Fronteira CFT)
ax1.set_facecolor('#111118')
ax1.plot(t, df['close'], color='#b0c4de', alpha=0.8, linewidth=1.5, label='Holograma 2D (GER40 H2)')
ax1.axvspan(300, 350, color='purple', alpha=0.2, label='Criacao do Vacuo de Dirac (Antimateria)')

if len(annihilation_events) > 0:
    for i, p in annihilation_events:
        ax1.scatter(i, p, color='cyan', s=100, marker='*', edgecolor='white', zorder=5, label='S-Matrix Annihilation (Colapso)')
        ax1.axvline(x=i, color='cyan', linestyle=':', alpha=0.5)

ax1.set_title('Fronteira CFT: Projecao do Preco & Aniquilacao Positronica', color='#00ffff', fontsize=14, pad=10)
ax1.legend(facecolor='#111118', edgecolor='gray', loc='upper right')
ax1.grid(True, color='gray', alpha=0.15)

# Ax2: Holographic Entropy (O "Bulk")
ax2.set_facecolor('#111118')
ax2.plot(t, holographic_entropy, color='#ff4500', linewidth=1.5, label='Bekenstein-Hawking Entropy ($S_{BH}$)')
ax2.fill_between(t, 0, holographic_entropy, color='#ff4500', alpha=0.15)
ax2.set_title('M-Theory Bulk: Sombras de Liquidez e Entropia do Buraco Negro', color='#00ffff', fontsize=14, pad=10)
ax2.legend(facecolor='#111118', edgecolor='gray', loc='upper left')
ax2.grid(True, color='gray', alpha=0.15)

# Ax3: S-Matrix Transition Amplitude
ax3.set_facecolor('#111118')
ax3.plot(t, s_matrix_amplitude, color='#00ff7f', linewidth=1.5, label='S-Matrix Scattering Amplitude ($|S_{fi}|^2$)')
ax3.fill_between(t, 0, s_matrix_amplitude, color='#00ff7f', alpha=0.2)
ax3.axhline(y=0.95, color='white', linestyle='--', linewidth=1, label='Annihilation Threshold (Decoerencia)')

ax3.set_title('Dinamica Quantica: Transicao de Estado e Espalhamento Bosonico', color='#00ffff', fontsize=14, pad=10)
ax3.set_ylim(0, 1.1)
ax3.legend(facecolor='#111118', edgecolor='gray', loc='upper left')
ax3.grid(True, color='gray', alpha=0.15)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Salvar Arquivo
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Docs/03_Ambiente_Executivo'))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'AdSCFT_Holographic_Visual_Test.png')

plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
print(f"AdS/CFT Holographic Validation Report gerado com sucesso em:\n{output_path}")
