import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import matplotlib.colors as mcolors

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine')))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
            
    import qgc_engine
    MOCK_ENGINES = False
except ImportError as e:
    print(f"Warning: C++ engines not found ({e}). Using Mock for visual test.")
    MOCK_ENGINES = True

plt.style.use('dark_background')

# 1. Simular Dados do Mercado (H2)
N = 800
t = np.arange(N)
np.random.seed(42)

price = np.zeros(N)
price[0] = 18000.0

for i in range(1, N):
    price[i] = price[i-1] + np.random.normal(0, 2.5)

# Forçar uma queda e um OB de alta massivo no inicio
price[100:150] -= np.linspace(0, 50, 50)
price[150] = price[149] - 20
price[151:250] += np.linspace(0, 80, 99)

df = pd.DataFrame({'close': price})
df['open'] = df['close'].shift(1).fillna(price[0])
df['high'] = df[['open', 'close']].max(axis=1) + np.random.exponential(1.5, N)
df['low'] = df[['open', 'close']].min(axis=1) - np.random.exponential(1.5, N)
df['tick_volume'] = np.random.randint(100, 1000, N)
df['atr'] = (df['high'] - df['low']).rolling(14).mean().bfill()

# Injeção de Vidro Quântico (Quantum Glass Condensate) na vela 150
df.loc[150, 'tick_volume'] = 150000.0 # Massa gravitacional gigantesca
qg_center = df.loc[150, 'low']

if not MOCK_ENGINES:
    engine = qgc_engine.QGCEngine()

# 3. Processar Decaimento (Hawking Radiation)
# Vamos avaliar o decaimento passo a passo para o plot
decay_history = np.zeros(N)
decay_history[:150] = np.nan
initial_mass = 150000.0
current_mass = initial_mass

for i in range(151, N):
    dist = abs(df.loc[i, 'close'] - qg_center)
    local_vol = df.loc[i, 'atr']
    
    lambda_decay = 0.005 # Evaporação natural pelo tempo
    if local_vol > 0:
        prox = max(0.0, 1.0 - (dist / (local_vol * 3.0)))
        lambda_decay += 0.05 * prox
        
    current_mass = current_mass * np.exp(-lambda_decay)
    
    if current_mass < (initial_mass * 0.1): # Evaporou
        current_mass = 0
        
    decay_history[i] = current_mass

# 4. Renderização Visual Cyber-Holográfica
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
fig.patch.set_facecolor('#0a0a0f')

fig.suptitle('NEXUS-QUANT :: QUANTUM LIQUIDITY GLASS & HAWKING DECAY', fontsize=20, color='white', fontweight='bold', y=0.95)

# --- AX1: Gráfico de Preço e Fitas de Decaimento ---
ax1.set_facecolor('#111118')
ax1.plot(t, df['close'], color='#b0c4de', alpha=0.7, linewidth=1.2, label='Price Action (Holograma)')

# Ponto de Ignição do QLG
ax1.scatter(150, df.loc[150, 'low'], color='#ff00ff', s=200, marker='*', edgecolor='white', zorder=5, label='Singularidade Inicial (QLG Genesis)')

# Renderizar a linha de decaimento (Neon Cyan/Magenta que afina com o tempo)
# Normalizar espessura baseada na massa
valid_idx = np.where(decay_history > 0)[0]
if len(valid_idx) > 0:
    alphas = decay_history[valid_idx] / initial_mass
    linewidths = alphas * 10.0 # Espessura máxima 10
    
    # Desenhar linha segmentada com alpha e espessura variando
    for i in range(len(valid_idx) - 1):
        idx = valid_idx[i]
        next_idx = valid_idx[i+1]
        a = max(0.1, alphas[i])
        lw = max(0.5, linewidths[i])
        ax1.plot([idx, next_idx], [qg_center, qg_center], color='#00ffff', alpha=a, linewidth=lw, solid_capstyle='round')

ax1.set_title('Topologia: Evaporacao Isotopica de Zonas Institucionais', color='#00ffff', fontsize=14, pad=10)
ax1.legend(facecolor='#111118', edgecolor='gray', loc='upper left')
ax1.grid(True, color='gray', alpha=0.1)

# --- AX2: Massa Residual (Termodinâmica) ---
ax2.set_facecolor('#111118')
# Plotar massa
ax2.plot(t, decay_history, color='#ff00ff', linewidth=2, label='Massa Residual ($M(t)$)')
ax2.fill_between(t, 0, decay_history, color='#ff00ff', alpha=0.2)

# Linha de morte (Threshold de 10%)
death_line = initial_mass * 0.1
ax2.axhline(y=death_line, color='red', linestyle='--', linewidth=1, label='Limite de Evaporacao (Hawking Death)')

ax2.set_title('Radiacao Hawking: Decaimento Gravitacional da Singularidade', color='#ff00ff', fontsize=12, pad=10)
ax2.legend(facecolor='#111118', edgecolor='gray', loc='upper right')
ax2.set_ylim(0, initial_mass * 1.1)
ax2.grid(True, color='gray', alpha=0.1)

plt.tight_layout(rect=[0, 0.03, 1, 0.90])

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Docs/03_Ambiente_Executivo'))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'QGC_Hawking_Decay_Visual_Test.png')

plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
print(f"QGC Visual Validation Report gerado com sucesso em:\n{output_path}")