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
        
        # Modo Agnóstico: Se não há símbolo, apenas confirmamos a saúde da API
        if self.symbol is None:
            return True
            
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
        Otimizado para economia de RAM (Stream-and-Flush).
        """
        import gc
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🧠 Iniciando Brain Scan Estrutural...")
        
        for name, tf in self.timeframes.items():
            print(f"Extraindo Memória Histórica: {name}...")
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            
            if rates is None or len(rates) == 0:
                print(f"Erro ao obter dados de {name}")
                continue
                
            # Cria DataFrame e processa imediatamente
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Armazenamento em Parquet (Limpeza de memória após gravação)
            file_name = f"{self.data_path}{self.symbol}_{name}.parquet"
            df.to_parquet(file_name)
            
            # Limpeza agressiva: o bot lerá do Parquet ou de cópias sob demanda
            del df
            del rates
            gc.collect() 
            
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ✅ Sincronização de Memória Histórica Completa.")
        return True # Retorna status em vez de snapshot pesado

    def get_realtime_memory(self):
        """Mantém a memória gradual conforme o mercado se move."""
        # Implementação de stream de ticks para memória de curto prazo
        tick = mt5.symbol_info_tick(self.symbol)
        return tick._asdict()

    def thermodynamic_sl_tp(self, r_score, current_price, atr, plasma_zones, schrodinger_density, cloud_tracker):
        """
        Co-Pilot Management v4.0 (Viscoelastic & Tunneling Boundary):
        Usa o CATASTROPHIC_SL no MT5 e gerencia o VIRTUAL_SL internamente via N-Core.
        """
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return
            
        digits = symbol_info.digits

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            self.virtual_sls.clear()
            return

        gravity_well_price = current_price
        gravity_valid = False
        if schrodinger_density is not None and cloud_tracker is not None:
            well_price = cloud_tracker.get_gravity_well_price(schrodinger_density)
            if well_price is not None:
                if abs(well_price - current_price) < (atr * 5.0):
                    gravity_well_price = well_price
                    gravity_valid = True
            
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
            open_price = pos.price_open
            
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
                if r_score == 1: # REGIME BULL
                    if gravity_valid and gravity_well_price > open_price + atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        new_tp = round(open_price + (atr * 4.0), digits)
                    
                    logical_sl = round(plasma_floor - (atr * 1.5), digits)
                    self.virtual_sls[ticket] = logical_sl
                    catastrophic_sl = round(pos_price - (atr * 8.8), digits)
                    
                    if current_sl == 0.0 or catastrophic_sl > current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 2: # REGIME BEAR (CONTRÁRIO)
                    emergency_sl = round(pos_price - (atr * 2.5), digits)
                    self.virtual_sls[ticket] = emergency_sl
                    catastrophic_sl = round(pos_price - (atr * 4.0), digits)
                    if current_sl == 0.0 or catastrophic_sl > current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                        
                else: # REGIME NEUTRO (0)
                    if current_sl == 0.0:
                        request["sl"] = round(open_price - (atr * 5.0), digits)
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = round(open_price + (atr * 5.0), digits)
                        modified = True

            # --- PROTEÇÃO PARA POSIÇÕES VENDIDAS (BEAR) ---
            elif order_type == mt5.ORDER_TYPE_SELL:
                if r_score == 2: # REGIME BEAR
                    if gravity_valid and gravity_well_price < open_price - atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        new_tp = round(open_price - (atr * 4.0), digits)
                    
                    logical_sl = round(plasma_ceiling + (atr * 1.5), digits)
                    self.virtual_sls[ticket] = logical_sl
                    catastrophic_sl = round(pos_price + (atr * 8.8), digits)
                    
                    if current_sl == 0.0 or catastrophic_sl < current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 1: # REGIME BULL (CONTRÁRIO)
                    emergency_sl = round(pos_price + (atr * 2.5), digits)
                    self.virtual_sls[ticket] = emergency_sl
                    catastrophic_sl = round(pos_price + (atr * 4.0), digits)
                    if current_sl == 0.0 or catastrophic_sl < current_sl:
                        request["sl"] = catastrophic_sl
                        modified = True
                        
                else: # REGIME NEUTRO (0)
                    if current_sl == 0.0:
                        request["sl"] = round(open_price + (atr * 5.0), digits)
                        modified = True
                    if current_tp == 0.0:
                        request["tp"] = round(open_price - (atr * 5.0), digits)
                        modified = True
                        
            if modified:
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ⚠️ NEXUS DEFENSE REJEITADO: Cód {result.retcode} na Ordem {ticket}")
                else:
                    v_sl = self.virtual_sls.get(ticket, "N/A")
                    # print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🛡️ SHIELD v4.1 Ativado em {ticket}. MT5 SL={request['sl']} | Virtual SL={v_sl} | TP={request['tp']}")

    def close_position(self, ticket, is_buy):
        """Fecha uma posição no mercado."""
        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info: return False
        
        pos = mt5.positions_get(ticket=ticket)
        if not pos: return False
        pos = pos[0]

        price = mt5.symbol_info_tick(self.symbol).bid if is_buy else mt5.symbol_info_tick(self.symbol).ask
        action_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": action_type,
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
        """
        Avalia se o preço cruzou o SL Virtual (Lógico).
        Se cruzou, aplica os cálculos de fluido não-newtoniano (Deborah Number)
        e tunelamento quântico para decidir se colapsa a onda (fecha o trade)
        ou se estica a fronteira viscoelástica (ignora o wick).
        """
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions or len(positions) == 0: return
        
        current_price = df['close'].iloc[-1]
        
        for pos in positions:
            ticket = pos.ticket
            if ticket not in self.virtual_sls: continue
            
            logical_sl = self.virtual_sls[ticket]
            order_type = pos.type
            
            is_breached = False
            if order_type == mt5.ORDER_TYPE_BUY and current_price <= logical_sl:
                is_breached = True
            elif order_type == mt5.ORDER_TYPE_SELL and current_price >= logical_sl:
                is_breached = True
                
            if is_breached:
                # 1. Fluido Viscoelástico Não-Newtoniano (LBM - Número de Deborah)
                # Assumimos que anomalias (wicks) costumam durar cerca de 1 timeframe. Estimativa de 15m = 900s.
                anomaly_duration = 900.0
                is_visco = lbm_tracker.evaluate_viscoelastic_shock(anomaly_duration) if lbm_tracker else False
                
                # 2. Efeito de Tunelamento Quântico (Schrodinger)
                vol_mass = df['tick_volume'].iloc[-1] if 'tick_volume' in df.columns else 100.0
                # A barreira é proporcional à distância do SL. Preço atual como partícula.
                barrier_e = abs(logical_sl - df['close'].iloc[-2])
                particle_e = abs(current_price - df['close'].iloc[-2])
                tunnel_prob = cloud_tracker.check_quantum_tunneling(barrier_e, particle_e, vol_mass * 0.001) if cloud_tracker else 1.0
                is_tunneling = tunnel_prob > 0.5
                
                if is_topological_collapsed:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🚨 [COLAPSO ESTRUTURAL METRICO] Malha CYT rompida! Fechando posição {ticket}.")
                    self.close_position(ticket, order_type == mt5.ORDER_TYPE_BUY)
                    self.virtual_sls.pop(ticket, None)
                elif is_visco or is_tunneling:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🌊 [FRONTEIRA VISCOELÁSTICA] Posição {ticket} rompeu SL virtual em {current_price}, mas foi absorvido! Tunelamento: {tunnel_prob*100:.1f}% | Visco: {is_visco} -> TRADE MANTIDO.")
                else:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 💥 [DECOERÊNCIA QUÂNTICA] Volume massivo rompeu a barreira {logical_sl}. Fechando posição {ticket}.")
                    self.close_position(ticket, order_type == mt5.ORDER_TYPE_BUY)
                    self.virtual_sls.pop(ticket, None)

    def render_danger_zones(self, danger_zones_array, time_array, threshold=50.0):
        """
        Renderiza Zonas de Perigo (Calabi-Yau) no MetaTrader 5.
        Desenha retângulos verticais ou linhas vermelhas nos tempos onde o danger_score > threshold.
        """
        current_time = int(time.time())
        window_start = current_time - (3600 * 24 * 7) # Útima semana

        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🚨 Renderizando Zonas de Perigo CYT no MT5...")

        if len(danger_zones_array) != len(time_array):
            print("Erro: Array de zonas de perigo e array de tempo incompatíveis.")
            return

        export_path = os.path.join(self.data_path, "cyt_danger_map.csv")
        try:
            df = pd.DataFrame({
                'time': time_array,
                'danger_score': danger_zones_array
            })
            df_filtered = df[df['danger_score'] > threshold]
            df_filtered.to_csv(export_path, index=False)
            print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🚨 Mapa de Zonas de Perigo exportado para {export_path}")
        except Exception as e:
            print(f"Erro ao exportar mapa de perigo: {e}")

    def shutdown(self):
        mt5.shutdown()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Teste da MT5 Bridge")
    parser.add_argument("--symbol", type=str, default=None, help="Symbol to test (None = wait)")
    args = parser.parse_args()

    bridge = MT5NeuralBridge(args.symbol)
    if bridge.initialize():
        bridge.fetch_full_history(count=5000)
        bridge.shutdown()