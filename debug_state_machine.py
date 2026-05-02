import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import sys
import os

from Code.N_Core.quantum_indicators import QuantumIndicators

def run_debug():
    print("Iniciando Debug do Monólito...")
    if not mt5.initialize():
        print("Erro MT5")
        return
        
    rates = mt5.copy_rates_from_pos("GER40.cash", mt5.TIMEFRAME_M15, 0, 1000)
    if rates is None:
        print("Sem dados")
        return
        
    df = pd.DataFrame(rates)
    q = QuantumIndicators()
    
    prev_s = 0
    prev_c = 0
    
    window_calc = 200
    
    print("Processando...")
    for i in range(window_calc, len(df)):
        slice_df = df.iloc[i-window_calc:i+1]
        
        r, c = q.advanced_regime_score(slice_df, prev_s, prev_c)
        
        # O BUG ESTÁ AQUI: Se prev_s era 1 ou 2, e r virou 0, algo quebrou a regra do Titânio.
        if prev_s != 0 and r == 0:
            print(f"[{i}] COLAPSO DO MONÓLITO: Regime era {prev_s} e virou 0!")
            curr = slice_df.iloc[-1]
            ema_trend = df['close'].ewm(span=34, adjust=False).mean().iloc[i]
            ema_gravity = df['close'].ewm(span=200, adjust=False).mean().iloc[i]
            print(f" > Close: {curr['close']}, EMA34: {ema_trend:.2f}, EMA200: {ema_gravity:.2f}")
            
        # Se prev_s era 1 e virou 2, vamos ver se a Gravidade (EMA200) realmente cruzou.
        if prev_s == 1 and r == 2:
            print(f"[{i}] FLIP PARA BEAR: 1 -> 2")
            curr = slice_df.iloc[-1]
            ema_trend = df['close'].ewm(span=34, adjust=False).mean().iloc[i]
            ema_gravity = df['close'].ewm(span=200, adjust=False).mean().iloc[i]
            print(f" > Close: {curr['close']}, EMA34: {ema_trend:.2f}, EMA200: {ema_gravity:.2f}")
            
        if prev_s == 2 and r == 1:
            print(f"[{i}] FLIP PARA BULL: 2 -> 1")
            curr = slice_df.iloc[-1]
            ema_trend = df['close'].ewm(span=34, adjust=False).mean().iloc[i]
            ema_gravity = df['close'].ewm(span=200, adjust=False).mean().iloc[i]
            print(f" > Close: {curr['close']}, EMA34: {ema_trend:.2f}, EMA200: {ema_gravity:.2f}")

        prev_s, prev_c = r, c

    print("Concluído.")
    mt5.shutdown()

if __name__ == "__main__":
    run_debug()
