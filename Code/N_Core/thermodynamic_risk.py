import numpy as np
import pandas as pd

class ThermodynamicRiskManager:
    """
    Thermodynamic Risk Manager (TRM) v92.
    Gere o ciclo de vida da ordem através de entropia, velocidade e gravidade.
    Implementa o FTMO Shield e o Trailing de Ebulição.
    """
    
    def __init__(self, lot_size=1.0, commission=55.0):
        self.lot_size = lot_size
        self.commission = commission # Taxa FTMO Round Turn
        self.min_net_profit = 15.0   # Lucro garantido após trava de $70
        self.activation_threshold = 70.0 # Gatilho para o FTMO Shield

    def calculate_thermodynamics(self, df_slice):
        """
        Calcula a 'Temperatura' e 'Velocidade' do fluxo atual.
        """
        curr = df_slice.iloc[-1]
        prev = df_slice.iloc[-2]
        
        atr = (df_slice['high'] - df_slice['low']).rolling(14).mean().iloc[-1]
        
        # Velocidade: Mudança de preço por tick (simulado em M1)
        velocity = abs(curr['close'] - prev['close']) / (atr + 1e-9)
        
        # Entropia: Tamanho do pavio em relação ao corpo (Resfriamento)
        body = abs(curr['close'] - curr['open'])
        u_wick = curr['high'] - max(curr['open'], curr['close'])
        l_wick = min(curr['open'], curr['close']) - curr['low']
        
        entropy = (u_wick + l_wick) / (body + 1e-9)
        
        return {
            'velocity': velocity,
            'entropy': entropy,
            'atr': atr
        }

    def manage_active_trade(self, trade_data, df_slice):
        """
        Lógica de Trailing v103 (Protocolo Soberano - Deixe o Gigante Viver).
        Foco total em capturar o Deep Potential e ignorar o ruído de M1.
        """
        curr = df_slice.iloc[-1]
        entry_price = trade_data['entry_price']
        regime = trade_data['regime']
        
        # PnL de Pico do Candle Atual
        max_price = curr['high'] if regime == 1 else curr['low']
        max_pnl_candle = (max_price - entry_price) if regime == 1 else (entry_price - max_price)
        
        trade_data['highest_pnl'] = max(trade_data.get('highest_pnl', 0), max_pnl_candle)
        mfe = trade_data['highest_pnl']

        stats = self.calculate_thermodynamics(df_slice)
        new_sl = trade_data['sl']
        should_exit = False
        exit_reason = ""
        exit_price = curr['close']

        # 1. TRAVA DE SOBREVIVÊNCIA v103
        # Só move o SL para o lucro líquido após $250 de lucro bruto (Espaço para o Gigante)
        if mfe >= 250.0 and not trade_data.get('shield_active', False):
            lock_offset = self.commission + 50.0 # Trava $50 líquidos
            new_sl = entry_price + lock_offset if regime == 1 else entry_price - lock_offset
            trade_data['shield_active'] = True
            # print("> GIGANTE VALIDADO: Proteção Ativada.")

        # 2. TRAILING DE ELITE (v103)
        if mfe > 800.0:
            # Trava 85% do lucro (O Gigante já está maduro)
            locked = mfe * 0.85
            potential_sl = entry_price + locked if regime == 1 else entry_price - locked
            new_sl = max(new_sl, potential_sl) if regime == 1 else min(new_sl, potential_sl)
        elif mfe > 400.0:
            # Trava 60% do lucro
            locked = mfe * 0.60
            potential_sl = entry_price + locked if regime == 1 else entry_price - locked
            new_sl = max(new_sl, potential_sl) if regime == 1 else min(new_sl, potential_sl)

        # 3. VERIFICAÇÃO INTRA-CANDLE
        if regime == 1:
            if curr['low'] <= new_sl: 
                should_exit = True; exit_reason = "STOP_LOSS/TRAIL"; exit_price = new_sl
            elif curr['high'] >= trade_data['tp']: 
                should_exit = True; exit_reason = "TAKE_PROFIT"; exit_price = trade_data['tp']
        else:
            if curr['high'] >= new_sl: 
                should_exit = True; exit_reason = "STOP_LOSS/TRAIL"; exit_price = new_sl
            elif curr['low'] <= trade_data['tp']: 
                should_exit = True; exit_reason = "TAKE_PROFIT"; exit_price = trade_data['tp']

        # 4. COLAPSO DE ENTROPIA v103 (Só sai se houver lucro massivo e rejeição extrema)
        if not should_exit and mfe > 300.0 and stats['entropy'] > 5.0:
            should_exit = True
            exit_reason = "THERMAL_COLLAPSE (Terminal Wick)"
            exit_price = curr['close']

        final_gross = (exit_price - entry_price) if regime == 1 else (entry_price - exit_price)

        return {
            'new_sl': new_sl, 'should_exit': should_exit,
            'exit_reason': exit_reason, 'exit_price': exit_price,
            'gross_pnl': final_gross
        }






