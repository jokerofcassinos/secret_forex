import numpy as np

def sim_qrw(bias):
    num_positions = 201
    center = 100
    state = np.zeros((num_positions, 2), dtype=complex)
    
    # Symmetric initial state
    state[center, 0] = 1.0 / np.sqrt(2)
    state[center, 1] = 1.0 / np.sqrt(2)
    
    for _ in range(50):
        new_state = np.zeros((num_positions, 2), dtype=complex)
        
        theta = np.pi/4
        
        C00 = np.cos(theta)
        C01 = 1j * np.sin(theta) * np.exp(1j * bias)
        C10 = 1j * np.sin(theta) * np.exp(-1j * bias)
        C11 = np.cos(theta)
        
        for i in range(num_positions):
            if np.abs(state[i, 0]) < 1e-10 and np.abs(state[i, 1]) < 1e-10: continue
            
            val0 = C00 * state[i, 0] + C01 * state[i, 1]
            val1 = C10 * state[i, 0] + C11 * state[i, 1]
            
            if i - 1 >= 0: new_state[i - 1, 0] += val0
            if i + 1 < num_positions: new_state[i + 1, 1] += val1
            
        state = new_state
        
    expected_val = 0.0
    for i in range(num_positions):
        prob = np.abs(state[i, 0])**2 + np.abs(state[i, 1])**2
        expected_val += (i - center) * prob
        
    return expected_val

print("Baseline (0):", sim_qrw(0.0))
print("Bull (+0.1):", sim_qrw(0.1))
print("Bear (-0.1):", sim_qrw(-0.1))
