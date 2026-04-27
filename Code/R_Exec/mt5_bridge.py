import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime
import time

class MT5NeuralBridge:
    def __init__(self, symbol="GER40.cash"):
        self.symbol = symbol
        self.timeframes = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        self.data_path = "Data/Historical/"
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def initialize(self):
        """Inicializa a conexão com o terminal MT5."""
        if not mt5.initialize():
            print(f"Falha ao inicializar MT5: {mt5.last_error()}")
            return False
        
        # Garantir que o símbolo está visível
        if not mt5.symbol_select(self.symbol, True):
            print(f"Símbolo {self.symbol} não encontrado.")
            return False
        
        print(f"NEXUS Bridge conectada ao {self.symbol}")
        return True

    def fetch_full_history(self, count=10000):
        """
        Extrai o contexto histórico completo de todos os timeframes.
        Este é o 'Brain Scan' inicial do mercado.
        """
        brain_snapshot = {}
        
        for name, tf in self.timeframes.items():
            print(f"Extraindo Memória Histórica: {name}...")
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            
            if rates is None or len(rates) == 0:
                print(f"Erro ao obter dados de {name}")
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Armazenamento em Parquet para ultra-velocidade
            file_name = f"{self.data_path}{self.symbol}_{name}.parquet"
            df.to_parquet(file_name)
            brain_snapshot[name] = df
            
        print("Sincronização de Memória Histórica Completa.")
        return brain_snapshot

    def get_realtime_memory(self):
        """Mantém a memória gradual conforme o mercado se move."""
        # Implementação de stream de ticks para memória de curto prazo
        tick = mt5.symbol_info_tick(self.symbol)
        return tick._asdict()

    def trailing_sl_tp(self, r_score, ema_trend, ema_macro, atr):
        """
        Co-Pilot Management: Gerencia dinamicamente o SL/TP das ordens abertas manualmente.
        Se o usuário abre a ordem a favor da Caixa (Regime), a máquina defende a posição 
        usando a EMA Macro ou EMA Trend como escudo termodinâmico.
        """
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return
            
        digits = symbol_info.digits

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            return
        
        for pos in positions:
            ticket = pos.ticket
            order_type = pos.type # 0 = BUY, 1 = SELL
            current_sl = pos.sl
            current_tp = pos.tp
            current_price = pos.price_current
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": self.symbol,
                "sl": current_sl,
                "tp": current_tp,
            }
            modified = False
            
            # --- PROTEÇÃO PARA POSIÇÕES COMPRADAS (BULL) ---
            if order_type == mt5.ORDER_TYPE_BUY:
                if r_score == 1:
                    new_sl = round(ema_trend - (atr * 1.5), digits)
                    new_tp = round(current_price + (atr * 10.0), digits) # Target Sideral
                    
                    if current_sl == 0.0 or new_sl > current_sl:
                        if current_price > new_sl:
                            request["sl"] = new_sl
                            modified = True
                    
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 2:
                    emergency_sl = round(current_price - (atr * 0.5), digits)
                    if current_sl == 0.0 or emergency_sl > current_sl:
                        request["sl"] = emergency_sl
                        modified = True

            # --- PROTEÇÃO PARA POSIÇÕES VENDIDAS (BEAR) ---
            elif order_type == mt5.ORDER_TYPE_SELL:
                if r_score == 2:
                    new_sl = round(ema_trend + (atr * 1.5), digits)
                    new_tp = round(current_price - (atr * 10.0), digits) # Target Sideral
                    
                    if current_sl == 0.0 or new_sl < current_sl:
                        if current_price < new_sl:
                            request["sl"] = new_sl
                            modified = True
                            
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 1:
                    emergency_sl = round(current_price + (atr * 0.5), digits)
                    if current_sl == 0.0 or emergency_sl < current_sl:
                        request["sl"] = emergency_sl
                        modified = True
                        
            if modified:
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ⚠️ NEXUS DEFENSE REJEITADO: Cód {result.retcode} - Não foi possível setar SL={request['sl']} TP={request['tp']} na Ordem {ticket}")
                else:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🛡️ NEXUS DEFENSE: Armadura ativada na posição {ticket}. SL={request['sl']} TP={request['tp']}")

    def shutdown(self):
        mt5.shutdown()

if __name__ == "__main__":
    # Teste de Conexão e Extração
    bridge = MT5NeuralBridge("BTCUSD")
    if bridge.initialize():
        bridge.fetch_full_history(count=5000)
        bridge.shutdown()
