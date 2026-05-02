import pandas as pd
import numpy as np
from Code.N_Core.quantum_indicators import QuantumIndicators

df = pd.DataFrame({
    'open': np.linspace(100, 200, 500) + np.random.normal(0, 2, 500),
    'high': np.linspace(100, 200, 500) + 10,
    'low': np.linspace(100, 200, 500) - 10,
    'close': np.linspace(100, 200, 500) + 5,
    'time': np.arange(500) * 300
})

df.loc[120, 'close'] = df.loc[120, 'open'] + 50 # Massive bull candle
prev_s = 0
prev_c = 0
q = QuantumIndicators()
scores = []

for i in range(120, len(df)):
    r, c = q.advanced_regime_score(df.iloc[i-120:i+1], prev_s, prev_c)
    scores.append(r)
    prev_s, prev_c = r, c

print(f"Unique scores: {set(scores)}")
print(f"Contains 0? {0 in scores}")
zero_count = scores.count(0)
print(f"Total 0s: {zero_count}")
