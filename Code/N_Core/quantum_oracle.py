import numpy as np
from typing import Dict, List

class QuantumOracle:
    """
    Quantum Oracle v2.0: O Simulador Dimensional.
    FIX P1-14: Monte Carlo agora suporta SELL (target < price).
    """
    
    def __init__(self, simulations: int = 10000):
        self.simulations = simulations

    def run_monte_carlo(self, current_price: float, volatility: float, target: float, stop: float, steps: int = 50) -> float:
        """
        FIX P1-14: Suporta ambas as direções (BUY e SELL).
        BUY: target > current_price, stop < current_price
        SELL: target < current_price, stop > current_price
        """
        returns = np.random.normal(0, volatility, (self.simulations, steps))
        price_paths = current_price * np.exp(np.cumsum(returns, axis=1))
        
        is_buy = target > current_price
        
        success_count = 0
        for path in price_paths:
            if is_buy:
                hit_target = np.where(path >= target)[0]
                hit_stop = np.where(path <= stop)[0]
            else:
                # FIX P1-14: Inverted comparison for SELL trades
                hit_target = np.where(path <= target)[0]
                hit_stop = np.where(path >= stop)[0]
            
            if len(hit_target) > 0:
                if len(hit_stop) == 0 or hit_target[0] < hit_stop[0]:
                    success_count += 1
                    
        return success_count / self.simulations

    def analyze_multidimensional_sync(self, m1_data, m5_data, m15_data) -> Dict:
        # TODO: Implementar lógica de correlação dimensional
        return {"sync_score": 0.85, "status": "RESONANCE_DETECTED"}

if __name__ == "__main__":
    oracle = QuantumOracle()
    # Test BUY
    prob_buy = oracle.run_monte_carlo(100, 0.001, 105, 95)
    print(f"BUY Prob: {prob_buy*100:.2f}%")
    # Test SELL
    prob_sell = oracle.run_monte_carlo(100, 0.001, 95, 105)
    print(f"SELL Prob: {prob_sell*100:.2f}%")
