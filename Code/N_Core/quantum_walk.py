import numpy as np
import sys
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))

try:
    root_path = os.path.dirname(os.path.dirname(current_dir))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)
    if os.name == 'nt':
        os.add_dll_directory(root_path)
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)

    import qrw_engine
except ImportError as e:
    print(f"WARNING: qrw_engine C++ module not found. Error: {e}")

class QRWTracker:
    """
    N-Core Agent: Quantum Random Walk (QRW) ASI-5
    Opera via Matriz Unitária SU(2) e Amplitudes Complexas para previsão HFT com Paralelização OMP.
    Agora de forma Stateful com Memória Neural de Onda.
    """
    def __init__(self, positions=401):
        try:
            self.engine = qrw_engine.QRWEngine(positions)
            self.is_active = True
        except (NameError, AttributeError) as e:
            print(f"❌ QRWTracker :: Erro de Interface: {e}")
            self.is_active = False
            self.engine = None
            
        self.num_positions = positions
        self.last_skew = 0.0
        self.scale_factor = 0.005
        self.history_max_probs = []

    def process_market_slice(self, df_slice):
        if not self.is_active or len(df_slice) < 50:
            return 0.0, "OFFLINE"

        deltas = df_slice['close'].diff().fillna(0).values[-50:]
        volumes = df_slice['tick_volume'].values[-50:]
        
        self.last_skew = self.engine.update_and_get_skew(deltas, volumes, self.scale_factor)
        
        return self.last_skew, "QUANTUM_STABILITY"

    def project_future_horizon(self, df_slice, steps=100):
        if not self.is_active or len(df_slice) < 14:
            return {"bias": "NEUTRAL", "max_prob": 0.0, "is_bimodal": False, "distribution": np.array([])}

        current_price = df_slice['close'].iloc[-1]
        
        tr = df_slice['high'] - df_slice['low']
        atr = tr.rolling(min(14, len(df_slice))).mean().iloc[-1]
        if pd.isna(atr) or atr < 1e-9: atr = 1.0

        body = df_slice['close'].iloc[-1] - df_slice['open'].iloc[-1]
        momentum = np.clip(body / atr, -3.0, 3.0)

        # Previsão ASI-5 (Stateful Step)
        res = self.engine.step(current_price, atr, momentum)
        
        prob_right = res["prob_right"]
        prob_left = res["prob_left"]
        max_prob = res["max_prob"]
        dist = res["distribution"]

        # Limite Dinâmico Termodinâmico (Colapso)
        self.history_max_probs.append(max_prob)
        if len(self.history_max_probs) > 100:
            self.history_max_probs.pop(0)

        mu = np.mean(self.history_max_probs) if len(self.history_max_probs) > 5 else 0.0
        sigma = np.std(self.history_max_probs) if len(self.history_max_probs) > 5 else 0.0
        threshold = mu + 1.5 * sigma
        
        bias_str = "NEUTRAL"
        is_bimodal = False

        if max_prob > threshold and max_prob > 0.05:
            if prob_right > prob_left * 2.0:
                bias_str = "BULLISH_BIAS"
            elif prob_left > prob_right * 2.0:
                bias_str = "BEARISH_BIAS"

        if prob_right >= 0.05 and prob_left >= 0.05 and abs(prob_right - prob_left) < 0.02:
            if bias_str == "NEUTRAL": is_bimodal = True

        return {"bias": bias_str, "max_prob": max_prob, "is_bimodal": is_bimodal, "distribution": dist}

    def get_probability_cloud(self):
        if not self.is_active: return []
        return self.engine.get_probability_distribution()

if __name__ == "__main__":
    print("QRW Predictive Engine ASI-5 (Adaptive SU(2) Unitary Matrix) loaded.")
