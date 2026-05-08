import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime
import time

class MT5NeuralBridge:
    def __init__(self, symbol=None):
        self.symbol = symbol
        self.last_sec_alert = False # State tracker para logs
        self.virtual_sls = {} # Armazena os Stop Loss Lógicos/Dimensionais
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
        
        if self.symbol is None:
            return True
            
        if not mt5.symbol_select(self.symbol, True):
            print(f"Símbolo {self.symbol} não encontrado.")
            return False
        
        print(f"NEXUS Bridge conectada ao {self.symbol}")
        return True

    def fetch_full_history(self, count=10000):
        import gc
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🧠 Iniciando Brain Scan Estrutural...")
        for name, tf in self.timeframes.items():
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            if rates is None or len(rates) == 0: continue
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            file_name = f"{self.data_path}{self.symbol}_{name}.parquet"
            df.to_parquet(file_name)
            del df; del rates; gc.collect() 
        return True

    def thermodynamic_sl_tp(self, r_score, current_price, atr, plasma_zones, schrodinger_density, cloud_tracker, precog_res=None):
        """
        Co-Pilot Management v4.2 (Singularity Horizon Injection):
        Usa o CATASTROPHIC_SL no MT5 e gerencia o VIRTUAL_SL internamente via Pre-Cognition C++.
        """
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None: return
        digits = symbol_info.digits

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            self.virtual_sls.clear()
            return

        plasma_floor = current_price - (atr * 5.0)
        plasma_ceiling = current_price + (atr * 5.0)
        if plasma_zones:
            plasma_floor = plasma_zones.get('bottom_level', plasma_floor)
            plasma_ceiling = plasma_zones.get('top_level', plasma_ceiling)
        
        for pos in positions:
            ticket = pos.ticket
            order_type = pos.type
            current_sl = pos.sl
            current_tp = pos.tp
            pos_price = pos.price_current
            open_price = pos.price_open
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": self.symbol,
                "sl": current_sl,
                "tp": current_tp,
            }
            modified = False
            
            # --- PROTEÇÃO BULL ---
            if order_type == mt5.ORDER_TYPE_BUY:
                if precog_res and precog_res.get('sl_bull_singular'):
                    logical_sl = round(precog_res['sl_bull_singular'], digits)
                else:
                    logical_sl = round(plasma_floor - (atr * 1.5), digits)
                
                self.virtual_sls[ticket] = logical_sl
                
                if r_score == 1: # TREND BULL
                    new_tp = round(open_price + (atr * 6.0), digits)
                    catastrophic_sl = round(logical_sl - (atr * 3.0), digits)
                    if current_sl == 0.0 or catastrophic_sl > current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                elif r_score == 2: # COUNTER TREND
                    emergency_sl = round(pos_price - (atr * 2.0), digits)
                    self.virtual_sls[ticket] = min(logical_sl, emergency_sl)
                    catastrophic_sl = round(self.virtual_sls[ticket] - (atr * 2.0), digits)
                    if current_sl == 0.0 or catastrophic_sl > current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True

            # --- PROTEÇÃO BEAR ---
            elif order_type == mt5.ORDER_TYPE_SELL:
                if precog_res and precog_res.get('sl_bear_singular'):
                    logical_sl = round(precog_res['sl_bear_singular'], digits)
                else:
                    logical_sl = round(plasma_ceiling + (atr * 1.5), digits)
                
                self.virtual_sls[ticket] = logical_sl

                if r_score == 2: # TREND BEAR
                    new_tp = round(open_price - (atr * 6.0), digits)
                    catastrophic_sl = round(logical_sl + (atr * 3.0), digits)
                    if current_sl == 0.0 or catastrophic_sl < current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                elif r_score == 1: # COUNTER TREND
                    emergency_sl = round(pos_price + (atr * 2.0), digits)
                    self.virtual_sls[ticket] = max(logical_sl, emergency_sl)
                    catastrophic_sl = round(self.virtual_sls[ticket] + (atr * 2.0), digits)
                    if current_sl == 0.0 or catastrophic_sl < current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
            
            if modified:
                mt5.order_send(request)

    def close_position(self, ticket, is_buy):
        pos = mt5.positions_get(ticket=ticket)
        if not pos: return False
        pos = pos[0]
        price = mt5.symbol_info_tick(self.symbol).bid if is_buy else mt5.symbol_info_tick(self.symbol).ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 10,
            "magic": 0,
            "comment": "NEXUS Quantum Collapse",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE

    def enforce_quantum_boundary(self, df, lbm_tracker, cloud_tracker, is_topological_collapsed):
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions: return
        current_price = df['close'].iloc[-1]
        for pos in positions:
            ticket = pos.ticket
            if ticket not in self.virtual_sls: continue
            logical_sl = self.virtual_sls[ticket]
            is_breached = (pos.type == mt5.ORDER_TYPE_BUY and current_price <= logical_sl) or \
                          (pos.type == mt5.ORDER_TYPE_SELL and current_price >= logical_sl)
            if is_breached:
                # Se rompeu o SL virtual, fechamos imediatamente para segurança de singularidade
                print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 💥 [SINGULARIDADE] Posição {ticket} rompeu barreira física em {current_price}. Colapsando trade.")
                self.close_position(ticket, pos.type == mt5.ORDER_TYPE_BUY)
                self.virtual_sls.pop(ticket, None)

    def shutdown(self):
        mt5.shutdown()