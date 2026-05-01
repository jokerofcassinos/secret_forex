import pandas as pd
import numpy as np
import sys
import os

sys.path.append(r'd:\AI Brain\US30')
from Code.N_Core.quantum_clouds import QuantumCloudTracker

def test_cloud():
    # Simple sine wave price
    prices = 18000 + np.sin(np.linspace(0, 10, 100)) * 50
    df = pd.DataFrame({
        'close': prices,
        'open': prices - 2,
        'high': prices + 5,
        'low': prices - 5,
        'tick_volume': np.random.randint(100, 500, 100)
    })
    
    tracker = QuantumCloudTracker(17900, 18100, 200)
    tracker.initialize_wave(prices[0])
    
    print("Step | Price | Center of Mass | Max Density | Total Prob | V(x) Min")
    for i in range(1, 100):
        density = tracker.step(df.iloc[:i])
        com = tracker.solver.get_center_of_mass()
        max_d = np.max(density)
        total_d = np.sum(density)
        V = tracker.generate_potential_from_volume_profile(df.iloc[:i])
        
        if i % 10 == 0:
            print(f"{i:4d} | {prices[i]:.1f} | {com:.1f} | {max_d:.5f} | {total_d:.5f} | {np.min(V):.5f}")

if __name__ == "__main__":
    test_cloud()
