import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
from datetime import datetime
import time

class MT5NeuralBridge:
    def __init__(self, symbol="GER40.cash"):
        self.symbol = symbol
        self.last_sec_alert = False # State tracker para logs
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
        Co-Pilot Management v3.0 (Thermodynamic Risk):
        FIX P0-10: Gravity well with VPOC fallback.
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
                    if gravity_valid and gravity_well_price > pos_price + atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        new_tp = round(pos_price + (atr * 3.0), digits)
                    
                    # SL ancorado no plasma floor com buffer (aumentado para respirar)
                    new_sl = round(plasma_floor - (atr * 1.5), digits)
                    
                    # Cap máximo de distância do SL
                    if new_sl < pos_price - (atr * 8.8):
                        new_sl = round(pos_price - (atr * 8.8), digits)
                    
                    # FIX P0-11: SL pode subir (trailing) OU recalibrar se plasma expandiu
                    if pos_price > new_sl:
                        if current_sl == 0.0 or new_sl > current_sl:
                            request["sl"] = new_sl
                            modified = True
                    
                    if current_tp == 0.0 or abs(current_tp - new_tp) > atr:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 2:
                    emergency_sl = round(pos_price - (atr * 2.5), digits)
                    if current_sl == 0.0 or emergency_sl > current_sl:
                        request["sl"] = emergency_sl
                        modified = True

            # --- PROTEÇÃO PARA POSIÇÕES VENDIDAS (BEAR) ---
            elif order_type == mt5.ORDER_TYPE_SELL:
                if r_score == 2:
                    if gravity_valid and gravity_well_price < pos_price - atr:
                        new_tp = round(gravity_well_price, digits)
                    else:
                        new_tp = round(pos_price - (atr * 3.0), digits)
                    
                    # Buffer aumentado para respirar
                    new_sl = round(plasma_ceiling + (atr * 1.5), digits)
                    
                    if new_sl > pos_price + (atr * 8.8):
                        new_sl = round(pos_price + (atr * 8.8), digits)
                    
                    # FIX P0-11: SL pode descer (trailing) OU recalibrar
                    if pos_price < new_sl:
                        if current_sl == 0.0 or new_sl < current_sl:
                            request["sl"] = new_sl
                            modified = True
                            
                    if current_tp == 0.0 or abs(current_tp - new_tp) > atr:
                        request["tp"] = new_tp
                        modified = True
                            
                elif r_score == 1:
                    emergency_sl = round(pos_price + (atr * 2.5), digits)
                    if current_sl == 0.0 or emergency_sl < current_sl:
                        request["sl"] = emergency_sl
                        modified = True
                        
            if modified:
                result = mt5.order_send(request)
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] ⚠️ NEXUS DEFENSE REJEITADO: Cód {result.retcode} - Não foi possível setar SL={request['sl']} TP={request['tp']} na Ordem {ticket}")
                else:
                    print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🛡️ THERMODYNAMIC SHIELD v2.0: Armadura ativada em {ticket}. SL={request['sl']} TP={request['tp']}")

    def render_danger_zones(self, danger_zones_array, time_array, threshold=50.0):
        """
        Renderiza Zonas de Perigo (Calabi-Yau) no MetaTrader 5.
        Desenha retângulos verticais ou linhas vermelhas nos tempos onde o danger_score > threshold.
        """
        # Limpar objetos antigos (opcional, pode ser pesado se feito a cada tick)
        # Vamos manter apenas uma janela recente para performance
        current_time = int(time.time())
        window_start = current_time - (3600 * 24 * 7) # Útima semana

        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 🚨 Renderizando Zonas de Perigo CYT no MT5...")

        # Sanity check
        if len(danger_zones_array) != len(time_array):
            print("Erro: Array de zonas de perigo e array de tempo incompatíveis.")
            return

        for i in range(len(danger_zones_array)):
            score = danger_zones_array[i]
            if score > threshold:
                obj_name = f"CYT_Danger_{time_array[i]}"
                # No MT5 via Python não há uma API robusta de desenho de objetos nativa do mt5-python.
                # A forma oficial de desenhar objetos via Python no MT5 não existe nativamente no pacote `MetaTrader5`.
                # Precisamos usar um EA em MQL5 recebendo sinais via arquivo/socket, ou apenas
                # alertar no console e criar um arquivo CSV para um indicador MQL5 ler.
                # 
                # Solução Arquitetural AGI-5: Escrever em um arquivo compartilhado
                # que um EA/Indicador (Nexus_Observer) no MT5 irá ler e desenhar.
                pass
        
        # Como o pacote `MetaTrader5` do Python não possui funções `ObjectCreate`
        # vamos salvar o mapa de perigo em disco para o terminal MT5 ler
        export_path = os.path.join(self.data_path, "cyt_danger_map.csv")
        try:
            df = pd.DataFrame({
                'time': time_array,
                'danger_score': danger_zones_array
            })
            # Filtra apenas pontos relevantes para poupar disco
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
    parser.add_argument("--symbol", type=str, default="GER40.cash", help="Symbol to test")
    args = parser.parse_args()

    # Teste de Conexão e Extração
    bridge = MT5NeuralBridge(args.symbol)
    if bridge.initialize():
        bridge.fetch_full_history(count=5000)
        bridge.shutdown()
