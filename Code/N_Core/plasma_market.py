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
    import mhd_engine
except ImportError as e:
    print(f"WARNING: mhd_engine C++ module not found. Error: {e}")

class PlasmaMarketTracker:
    """
    N-Core Agent: Magnetohydrodynamics (MHD) v2.5 - Singularidade Holográfica
    Modela zonas de Stop Hunt como Plasma (Fluido Condutor) e Momentum como Campos Magnéticos.
    Utiliza a Relação de Bennett para prever o colapso do Z-Pinch.
    """
    def __init__(self):
        try:
            # Mu: Permeabilidade Magnética Institucional
            # Adiabatic_Idx: Razão de calores específicos do mercado
            self.engine = mhd_engine.MHDEngine(mu=1.2, adiabatic_idx=1.4)
            self.is_active = True
        except NameError:
            self.is_active = False
            
        self.in_zone = False
        self.zone_type = None 
        self.z_index_history = []
        self.magnetic_pressure = 0.0
        self.thermal_pressure = 0.0

    def scan_for_plasma_zones(self, df_slice, lookback=150):
        """
        Identifica 'Liquidity Pools' dinâmicos usando Kernel de Densidade ATR.
        Diferencia entre zonas frescas (Alta Energia) e exaustas.
        """
        if len(df_slice) < lookback:
            return {'top_level': 0, 'bottom_level': 0, 'top_density': 1, 'bottom_density': 1}

        recent = df_slice.tail(lookback)
        atr = (recent['high'] - recent['low']).mean()
        
        # Algoritmo de Agrupamento por Densidade (Holographic Scan)
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Encontra o nível com maior 'congestão' de sombras (Plasma Acumulado)
        # Usamos uma janela de 0.5 ATR para definir a espessura da membrana de plasma
        margin = atr * 0.5
        
        top_clusters = []
        bottom_clusters = []
        
        for p in highs[-50:]: # Foca nos últimos níveis para relevância temporal
            count = np.sum((highs > p - margin) & (highs < p + margin))
            top_clusters.append((p, count))
            
        for p in lows[-50:]:
            count = np.sum((lows > p - margin) & (lows < p + margin))
            bottom_clusters.append((p, count))
            
        # Seleciona as zonas com maior densidade institucional
        best_top = max(top_clusters, key=lambda x: x[1])
        best_bottom = max(bottom_clusters, key=lambda x: x[1])
        
        return {
            'top_level': best_top[0],
            'top_density': max(1.5, best_top[1] * 0.8), # Peso de confinamento
            'bottom_level': best_bottom[0],
            'bottom_density': max(1.5, best_bottom[1] * 0.8)
        }

    def process_tick(self, curr_candle, prev_candle, plasma_zones, atr=1.0):
        """
        Avança a simulação MHD v2.5.
        Calcula o equilíbrio entre Pressão Magnética (B^2/2mu) e Pressão Térmica (nkT).
        """
        if not self.is_active: return 0.0, "NO_DATA"

        curr_price = curr_candle['close']
        delta_price = curr_price - prev_candle['close']
        vol = curr_candle.get('tick_volume', 100)
        
        # 1. Cálculo de Pressões (Bennett Relation)
        # B (Magnetic Field) = Volume / Tempo
        # T (Temperature) = ATR (Entropia local)
        self.magnetic_pressure = (vol ** 2) / (2 * 1.2) # B^2 / 2mu
        self.thermal_pressure = atr * 100 # nkT (Escalado)
        
        # 2. Detecção de Membrana de Plasma (Holographic Horizon)
        # A zona não é uma linha, é uma curva Gaussiana
        dist_top = abs(curr_price - plasma_zones['top_level'])
        dist_bottom = abs(curr_price - plasma_zones['bottom_level'])
        threshold_dist = atr * 0.8 # Espessura da zona de captura
        
        in_top_plasma = dist_top < threshold_dist
        in_bottom_plasma = dist_bottom < threshold_dist

        # Máquina de Estado MHD
        if in_top_plasma and not self.in_zone:
            self.in_zone = True
            self.zone_type = "TOP_SWEEP"
            self.engine.reset_state()
            
        elif in_bottom_plasma and not self.in_zone:
            self.in_zone = True
            self.zone_type = "BOTTOM_SWEEP"
            self.engine.reset_state()
            
        elif not in_top_plasma and not in_bottom_plasma and self.in_zone:
            # O preço escapou da zona sem colapsar (Dissipação Térmica)
            self.in_zone = False
            self.zone_type = None
            self.engine.reset_state()

        if self.in_zone:
            # Z-Pinch: A compressão aumenta conforme a Pressão Magnética vence a Térmica
            z_density = plasma_zones['top_density'] if self.zone_type == "TOP_SWEEP" else plasma_zones['bottom_density']
            
            # Modificador de Compressão Quântica
            compression_boost = self.magnetic_pressure / (self.thermal_pressure + 1e-9)
            
            # Chama o motor C++ para resolver a equação de transporte MHD
            z_idx = self.engine.step_pinch(delta_price, vol * compression_boost, z_density)
            
            # Limita e suaviza o Z-Index para o HUD
            z_idx = np.clip(z_idx, 0, 100)
            self.z_index_history.append(z_idx)
            return z_idx, self.zone_type
            
        return 0.0, "NEUTRAL"

    def get_z_index_history(self):
        return self.z_index_history

if __name__ == "__main__":
    print("MHD Singularidade v2.5 - Módulo Carregado.")