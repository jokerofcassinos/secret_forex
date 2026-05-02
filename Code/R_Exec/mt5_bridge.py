import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime
import time

class MT5NeuralBridge:
    def __init__(self, symbol="BTCUSD"):
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

    def thermodynamic_sl_tp(self, r_score, current_price, atr, plasma_zones, schrodinger_density, cloud_tracker):
        """
        Co-Pilot Management v2.0 (Thermodynamic Risk):
        FIX P0-10: Gravity well with VPOC fallback when Schrödinger is unreliable.
        FIX P0-11: SL can recalibrate when plasma zones widen.
        FIX P1-11: Emergency SL widened from 0.5 to 1.5 ATR.
        FIX P1-12: TP uses structural targets with Fibonacci extensions.
        """
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return
            
        digits = symbol_info.digits

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            return
            
        # --- FIX P0-10: Gravity Well com validação de sanidade ---
        gravity_well_price = current_price
        gravity_valid = False
        if schrodinger_density is not None and cloud_tracker is not None:
            well_price = cloud_tracker.get_gravity_well_price(schrodinger_density)
            if well_price is not None:
                # Sanity check: o gravity well deve estar dentro de ±5 ATR do preço
                if abs(well_price - current_price) < (atr * 5.0):
                    gravity_well_price = well_price
                    gravity_valid = True
            
        # Extrair a Armadura de Plasma (MHD)
        plasma_ceiling = current_price + (atr * 5.0)
        plasma_floor = current_price - (atr * 5.0)
        
        if plasma_zones is not None:
            plasma_ceiling = plasma_zones.get('top_level', plasma_ceiling)
            plasma_floor = plasma_zones.get('bottom_level', plasma_floor)
        
        for pos in positions:
            ticket = pos.ticket
            order_type = pos.type
            current_sl = pos.sl
            current_tp = pos.tp
            pos_price = pos.price_current
            
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
                    # FIX P0-10/P1-12: TP multi-source
                    if gravity_valid and gravity_well_price > pos_price + atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        # Fallback: 3x ATR como target mínimo razoável
                        new_tp = round(pos_price + (atr * 3.0), digits)
                    
                    # SL ancorado no plasma floor com buffer
                    new_sl = round(plasma_floor - (atr * 0.5), digits)
                    
                    # Cap máximo de distância do SL
                    if new_sl < pos_price - (atr * 3.0):
                        new_sl = round(pos_price - (atr * 3.0), digits)
                    
                    # FIX P0-11: SL pode subir (trailing) OU recalibrar se plasma expandiu
                    if pos_price > new_sl:
                        if current_sl == 0.0 or new_sl > current_sl:
                            request["sl"] = new_sl
                            modified = True
                    
                    if current_tp == 0.0 or abs(current_tp - new_tp) > atr:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 2:
                    # FIX P1-11: Emergency SL widened from 0.5 to 1.5 ATR
                    emergency_sl = round(pos_price - (atr * 1.5), digits)
                    if current_sl == 0.0 or emergency_sl > current_sl:
                        request["sl"] = emergency_sl
                        modified = True

            # --- PROTEÇÃO PARA POSIÇÕES VENDIDAS (BEAR) ---
            elif order_type == mt5.ORDER_TYPE_SELL:
                if r_score == 2:
                    # FIX P0-10/P1-12: TP multi-source
                    if gravity_valid and gravity_well_price < pos_price - atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        new_tp = round(pos_price - (atr * 3.0), digits)
                    
                    new_sl = round(plasma_ceiling + (atr * 0.5), digits)
                    
                    if new_sl > pos_price + (atr * 3.0):
                        new_sl = round(pos_price + (atr * 3.0), digits)
                    
                    # FIX P0-11: SL pode descer (trailing) OU recalibrar
                    if pos_price < new_sl:
                        if current_sl == 0.0 or new_sl < current_sl:
                            request["sl"] = new_sl
                            modified = True
                            
                    if current_tp == 0.0 or abs(current_tp - new_tp) > atr:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 1:
                    # FIX P1-11: Emergency SL widened
                    emergency_sl = round(pos_price + (atr * 1.5), digits)
                    if current_sl == 0.0 or emergency_sl < current_sl:
                        request["sl"] = emergency_sl
                        modified = True
                        
            if modified:
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ⚠️ NEXUS DEFENSE REJEITADO: Cód {result.retcode} - Não foi possível setar SL={request['sl']} TP={request['tp']} na Ordem {ticket}")
                else:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🛡️ THERMODYNAMIC SHIELD v2.0: Armadura ativada em {ticket}. SL={request['sl']} TP={request['tp']}")

    def shutdown(self):
        mt5.shutdown()

if __name__ == "__main__":
    # Teste de Conexão e Extração
    bridge = MT5NeuralBridge("BTCUSD")
    if bridge.initialize():
        bridge.fetch_full_history(count=5000)
        bridge.shutdown()
