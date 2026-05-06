import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine/src/cyt')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../CPP_Engine')))

try:
    import cyt_engine
    MOCK_CYT = False
except ImportError:
    print("Warning: cyt_engine not found, using Mock for visual test.")
    MOCK_CYT = True

from market_qcd import MarketQCDTracker

plt.style.use('dark_background')

# 1. Simular Dados do GER40 (H2)
N = 1000
t = np.arange(N)

np.random.seed(42)
price = np.zeros(N)
price[0] = 18000.0

for i in range(1, N):
    if 200 < i < 250:
        price[i] = price[i-1] + np.random.normal(5, 2)  # Fissão UP
    elif 600 < i < 650:
        price[i] = price[i-1] - np.random.normal(5, 2)  # Fissão DOWN
    elif 800 < i < 820:
        price[i] = price[i-1] + np.random.normal(15, 5) # Anomalia topológica forte (Ruído HFT)
    else:
        price[i] = price[i-1] + np.random.normal(0, 1.5) # Consolidação / Range

# Gerar OHLCV
df = pd.DataFrame({'close': price})
df['open'] = df['close'].shift(1).fillna(price[0])
df['high'] = df[['open', 'close']].max(axis=1) + np.random.exponential(1, N)
df['low'] = df[['open', 'close']].min(axis=1) - np.random.exponential(1, N)
df['tick_volume'] = np.random.randint(100, 1000, N)

# Adicionar picos de volume durante as fissões
df.loc[200:250, 'tick_volume'] = df.loc[200:250, 'tick_volume'] * 3
df.loc[600:650, 'tick_volume'] = df.loc[600:650, 'tick_volume'] * 3
df.loc[800:820, 'tick_volume'] = df.loc[800:820, 'tick_volume'] * 5

# 2. Processar Market QCD
qcd = MarketQCDTracker(lookback_window=20)
confinement = np.zeros(N)
fission_signals = []

for i in range(20, N):
    window_df = df.iloc[:i]
    confinement[i] = qcd.calculate_confinement_force(window_df)
    sig = qcd.detect_fission(window_df)
    if "FISSION" in sig:
        fission_signals.append((i, sig, df['close'].iloc[i]))

# 3. Processar Ricci Flow (CYT Engine C++ ou Mock)
data_10d = np.zeros((10, N))
data_10d[0, :] = df['open'].values
data_10d[1, :] = df['high'].values
data_10d[2, :] = df['low'].values
data_10d[3, :] = df['close'].values
data_10d[4, :] = df['tick_volume'].values
data_10d[5, :] = df['close'].pct_change().bfill().values
data_10d[6, :] = (df['high'] - df['low']).values
data_10d[7, :] = df['close'].rolling(5).mean().bfill().values
data_10d[8, :] = df['tick_volume'].rolling(5).mean().bfill().values
data_10d[9, :] = (df['close'] - df['open']).values

if not MOCK_CYT:
    cyt = cyt_engine.CYTEngine()
    flow = cyt.analyze_manifold_flow(data_10d)
    ricci_deformation = flow["deformation"]
    danger_zones = cyt.calculate_danger_zones(data_10d, window=20, threshold=0.5)
else:
    # Mock do Ricci Flow usando proxy de curvatura (volatilidade + aceleração)
    ricci_deformation = np.zeros(N)
    danger_zones = np.zeros(N)
    for i in range(1, N):
        curvature = abs(data_10d[3, i] - data_10d[3, i-1]) * 2.0
        ricci_deformation[i] = curvature
        if i > 20:
            mean_curv = np.mean(ricci_deformation[i-20:i])
            if curvature > mean_curv * 2.5:
                danger_zones[i] = 100.0

# 4. Plotar Visual
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
fig.patch.set_facecolor('#0f0f0f')

# Título Principal
fig.suptitle('NEXUS-QUANT :: GEOMETRODINÂMICA (MGD) VALIDATION REPORT', fontsize=22, color='white', fontweight='bold')

# Ax1: Preço e Sinais de Fissão
ax1.set_facecolor('#1a1a1a')
ax1.plot(t, df['close'], color='#a9a9a9', alpha=0.8, linewidth=1.5, label='GER40 (H2) Simulated')
ax1.set_title('Topologia de Preço & Liberdade Assintótica (Fissão)', color='cyan', fontsize=14, pad=10)

# Plot Fission Points
for i, sig, p in fission_signals:
    color = 'lime' if 'UP' in sig else 'red'
    ax1.scatter(i, p, color=color, s=20, marker='o', alpha=0.7)

ax1.legend(facecolor='#1a1a1a', edgecolor='gray')
ax1.grid(True, color='gray', alpha=0.2)

# Ax2: Força de Confinamento (Market QCD)
ax2.set_facecolor('#1a1a1a')
ax2.plot(t, confinement, color='magenta', linewidth=1.5, label='Forca de Confinamento (Cordas Quanticas)')
ax2.fill_between(t, 0, confinement, color='magenta', alpha=0.15)
ax2.set_title('Market QCD: Tensao Institucional & Confinamento', color='cyan', fontsize=14, pad=10)

threshold = np.mean(confinement[20:]) + 2*np.std(confinement[20:])
ax2.axhline(y=threshold, color='orange', linestyle='--', linewidth=1, label='Asymptotic Threshold (Fissao)')
ax2.legend(facecolor='#1a1a1a', edgecolor='gray')
ax2.grid(True, color='gray', alpha=0.2)

# Ax3: Ricci Flow Deformation (C++)
ax3.set_facecolor('#1a1a1a')
ax3.plot(t, ricci_deformation, color='gold', linewidth=1.5, label='Curvatura de Ricci (Deformacao Topologica)')

# Colorir as danger zones
ax3.fill_between(t, 0, danger_zones, color='red', alpha=0.4, label='Danger Zones (Colapso Entropico / Ruido HFT)')

ax3.set_title('Topologia Diferencial: Fluxo de Ricci & Singularidades', color='cyan', fontsize=14, pad=10)
ax3.legend(facecolor='#1a1a1a', edgecolor='gray')
ax3.grid(True, color='gray', alpha=0.2)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Salvar
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Docs/03_Ambiente_Executivo'))
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'MGD_Ricci_QCD_Visual_Test.png')

plt.savefig(output_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
print(f"MGD Visual Validation Report gerado com sucesso em:\n{output_path}")
