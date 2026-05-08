import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Paths setup
project_root = r"d:\AI Brain\US30"
sys.path.append(os.path.join(project_root, 'Code', 'N_Core'))
sys.path.append(os.path.join(project_root, 'Code', 'CPP_Engine'))
sys.path.append(os.path.join(project_root, 'Code', 'CPP_Engine', 'bin'))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
    import schrodinger_engine
    from quantum_clouds import QuantumCloudTracker
except ImportError as e:
    print(f"Error loading engines: {e}")
    sys.exit(1)

# 1. Load Real Data
data_path = os.path.join(project_root, 'Data', 'Historical', 'GER40.cash_M5.parquet')
df = pd.read_parquet(data_path)
df = df.tail(1000) # Analyze last 1000 candles for performance

# 2. Setup Tracker
price_min = df['low'].min() * 0.999
price_max = df['high'].max() * 1.001
tracker = QuantumCloudTracker(price_min, price_max, bins=512)
tracker.initialize_wave(df['close'].iloc[0])

# 3. Simulation Loop
heatmaps = []
singularities = []
prices = []

print(f"Starting Schrodinger Cloud Analysis on {len(df)} candles...")

for i in range(20, len(df)):
    slice_df = df.iloc[i-20:i+1]
    density, reset = tracker.step(slice_df, dt=0.5, steps=2)
    
    if density is not None:
        heatmaps.append(density)
        metrics = tracker.get_singularity_metrics()
        singularities.append(metrics['singularity_strength'])
        prices.append(df['close'].iloc[i])
        
    if i % 100 == 0:
        print(f"Processed {i}/{len(df)} candles...")

# 4. Visualization
heatmaps = np.array(heatmaps).T # (Bins, Time)
time_axis = np.arange(len(prices))
price_axis = np.linspace(tracker.price_min, tracker.price_max, tracker.bins)

plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
fig.patch.set_facecolor('#0a0a0f')

# Ax1: Price + Heatmap
ax1.set_facecolor('#0a0a0f')
# Use pcolormesh for the heatmap
X, Y = np.meshgrid(time_axis, price_axis)
im = ax1.pcolormesh(X, Y, heatmaps, cmap='magma', shading='gouraud', alpha=0.8)
ax1.plot(time_axis, prices, color='cyan', linewidth=1, label='GER40 Close')

ax1.set_title('NEXUS-QUANT :: SCHRODINGER CLOUD HEATMAP (REAL DATA)', color='#00ffff', fontsize=16)
ax1.set_ylabel('Price (GER40)')
ax1.legend()

# Ax2: Singularity Strength (Collapse Indicator)
ax2.set_facecolor('#0a0a0f')
ax2.plot(time_axis, singularities, color='#ff4500', linewidth=1.5, label='Singularity Strength (Wave Collapse)')
ax2.axhline(y=0.04, color='white', linestyle='--', alpha=0.5, label='Collapse Threshold')
ax2.fill_between(time_axis, 0, singularities, color='#ff4500', alpha=0.2)
ax2.set_ylabel('Strength')
ax2.set_title('Singularity Metric: Institutional Coagulation', color='#00ffff', fontsize=12)
ax2.legend()

plt.tight_layout()
output_path = os.path.join(project_root, 'artifacts', 'schrodinger_heatmap_analysis.png')
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)
plt.savefig(output_path, dpi=150)
print(f"Analysis complete. Saved to {output_path}")
