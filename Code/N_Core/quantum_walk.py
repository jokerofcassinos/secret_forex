import numpy as np
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))

try:
    if os.name == 'nt':
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)
    import qrw_engine
except ImportError as e:
    print(f"WARNING: qrw_engine C++ module not found. Error: {e}")

class QRWTracker:
    """
    N-Core Agent: Quantum Random Walk (QRW) v3.0 [PERSISTENT]
    Decodes hidden accumulation/distribution using quantum phase persistence.
    """
    def __init__(self, positions=401, decoherence=0.995):
        try:
            self.engine = qrw_engine.QRWEngine(positions)
            self.engine.set_decoherence(decoherence)
            self.is_active = True
            self.last_processed_time = 0
        except NameError:
            self.is_active = False

    def process_qrw_skewness(self, df_slice, lookback=1):
        """
        Processa novos dados e mantém a função de onda viva.
        lookback=1 processa apenas o tick/barra mais recente para manter a coerência.
        """
        if not self.is_active or len(df_slice) < 5:
            return 0.0, "NONE"
            
        # Pega apenas as barras que ainda não foram processadas
        recent = df_slice.tail(lookback).copy()
        
        # Filtro de tempo para evitar re-processar a mesma barra
        current_time = recent.index[-1] if hasattr(recent.index, 'max') else 0
        if current_time <= self.last_processed_time and lookback == 1:
            return self.engine.get_skewness(), "STABLE"

        price_deltas = (recent['close'] - recent['open']).values.astype(np.float64)
        volumes = recent.get('tick_volume', pd.Series(np.ones(len(recent)))).values.astype(np.float64)
        
        # Calibração Absoluta: Fator de Escala Logarítmico amortecido pelo ATR
        tr = (df_slice['high'] - df_slice['low']).tail(14).mean()
        vol_mean = volumes.mean() if volumes.mean() > 0 else 1.0
        atr_scale = 1.0 / (tr * np.log1p(vol_mean) + 1e-9)
        
        # Injeção direta de RAM (Zero-Copy) no C++
        skewness = self.engine.update_and_get_skew(
            price_deltas, volumes, float(atr_scale)
        )
        
        self.last_processed_time = current_time
        
        # Thresholds calibrados para Skewness Normalizada (Z-Score Like)
        signal = "NEUTRAL"
        if skewness > 1.2:
            signal = "QUANTUM_ACCUMULATION_BULL"
        elif skewness < -1.2:
            signal = "QUANTUM_DISTRIBUTION_BEAR"
            
        return skewness, signal

if __name__ == "__main__":
    print("QRW Persistent Engine v3.0 module loaded.")