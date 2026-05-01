import numpy as np

def simulate(bias_list):
    num_positions = 201
    state = np.zeros((num_positions, 2), dtype=complex)
    
    # Init symmetric
    start = num_positions // 2
    state[start, 0] = 1.0 / np.sqrt(2.0)
    state[start, 1] = 1j / np.sqrt(2.0)
    
    for t in range(20):
        theta = np.pi/4 + bias_list[t] * np.pi/8
        C = np.array([[np.cos(theta), np.sin(theta)], [np.sin(theta), -np.cos(theta)]], dtype=complex)
        
        new_state = np.zeros((num_positions, 2), dtype=complex)
        for i in range(num_positions):
            if np.abs(state[i, 0]) == 0 and np.abs(state[i, 1]) == 0: continue
            val = C @ state[i]
            if i - 1 >= 0: new_state[i-1, 0] += val[0]
            if i + 1 < num_positions: new_state[i+1, 1] += val[1]
        state = new_state
        
    probs = np.abs(state[:,0])**2 + np.abs(state[:,1])**2
    
    expected_val = 0.0
    for i in range(num_positions):
        x = i - start
        expected_val += x * probs[i]
        
    variance = 0.0
    for i in range(num_positions):
        x = i - start
        variance += (x - expected_val)**2 * probs[i]
        
    skewness = 0.0
    if variance > 0:
        std = np.sqrt(variance)
        for i in range(num_positions):
            x = i - start
            skewness += ((x - expected_val)/std)**3 * probs[i]
            
    print(f"Bias Sum={sum(bias_list):.2f} -> Expected: {expected_val:.4f}, Skewness: {skewness:.4f}")

simulate([0.0]*20)
simulate([0.5]*20)
simulate([-0.5]*20)
simulate([0.8]*20)
simulate([-0.8]*20)
