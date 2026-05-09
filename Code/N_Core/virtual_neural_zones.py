import math

class AdaptiveNeuralZones:
    """
    Motor ANZ (Adaptive Neural Zones)
    Calcula dinamicamente as zonas de Stop Loss (SL) e Take Profit (TP) 
    com base nas propriedades termodinâmicas e topológicas do mercado,
    em vez de usar pontos fixos.
    """
    def __init__(self):
        self.active_positions = {}
        # active_positions = {
        #    "ticket_1": {"setup": "S7_TSUNAMI_MACRO", "direction": "LONG", "entry_price": 71000.0, "entry_time": ...}
        # }

    def register_position(self, ticket: str, setup_name: str, direction: str, entry_price: float):
        self.active_positions[ticket] = {
            "setup": setup_name,
            "direction": direction,
            "entry_price": entry_price,
            "highest_price": entry_price if direction == "LONG" else 0.0,
            "lowest_price": entry_price if direction == "SHORT" else float('inf')
        }

    def evaluate_zones(self, ctx: dict, current_price: float) -> dict:
        """
        Calcula os níveis dinâmicos de TP e SL para todas as posições ativas,
        utilizando Monte Carlo PreCognition para o SL Absoluto e QTE (Tunneling) para o TP.
        """
        zones = {}
        qho_state = ctx.get("qho_state", {})
        qho_shells = ctx.get("qho_shells", [])
        qte_prob = ctx.get("qte_prob", 0.0)
        qdd_f = ctx.get("qdd_fidelity", 0.0)
        atr = ctx.get("atr", 10.0)
        
        # PreCognition (SL Absoluto baseado em 500 simulações de falha de contenção MHD)
        precog_sl_long = ctx.get("precog_sl_long", current_price - atr * 3.0)
        precog_sl_short = ctx.get("precog_sl_short", current_price + atr * 3.0)

        for ticket, pos in self.active_positions.items():
            setup = pos["setup"]
            direction = pos["direction"]
            
            # Update high/low tracking for trailing
            if direction == "LONG":
                pos["highest_price"] = max(pos["highest_price"], current_price)
            else:
                pos["lowest_price"] = min(pos["lowest_price"], current_price)

            sl_price = precog_sl_long if direction == "LONG" else precog_sl_short
            tp_price = 0.0
            action = "HOLD"

            # ---------------------------------------------------------
            # 1. GESTÃO DE TAKE PROFIT DINÂMICO (QTE - Tunneling)
            # ---------------------------------------------------------
            # Se T > 0.85, o preço tem força para atravessar a próxima barreira de liquidez. Mantemos (HOLD).
            # Se T < 0.15, o preço vai ricochetear na barreira. Fechamos (EXIT).
            if qte_prob > 0.0 and qte_prob < 0.15:
                action = "EXIT_QTE_BOUNCE"

            # ---------------------------------------------------------
            # 2. OVERRIDES ESPECÍFICOS POR SETUP
            # ---------------------------------------------------------
            if setup == "S7_TSUNAMI_MACRO":
                # Gestão S7: SL Trailing Escorado no QHO shell n=3 (Dinâmico e mais apertado que o PreCognition)
                if len(qho_shells) > 3:
                    if direction == "LONG":
                        sl_price = max(sl_price, qho_shells[3]) # Pega o mais seguro (maior)
                        if current_price < sl_price:
                            action = "EXIT_SL_TRAILING"
                        if qdd_f < 0.0: # Decoerência dimensional
                            action = "EXIT_MACRO_BREAK"
                    else:
                        sl_price = min(sl_price, current_price + (atr * 3.0)) 
                        if current_price > sl_price:
                            action = "EXIT_SL_TRAILING"
                        if qdd_f > 0.0:
                            action = "EXIT_MACRO_BREAK"
                tp_price = 0.0 # Sem TP fixo, surfamos até a onda quebrar

            elif setup == "S4_HARMONIC_RESONANCE":
                if direction == "LONG":
                    sl_price = max(sl_price, current_price - (atr * 4.0))
                    tp_price = current_price + (atr * 2.0)
                else:
                    sl_price = min(sl_price, current_price + (atr * 4.0))
                    tp_price = current_price - (atr * 2.0)

            elif setup == "S5_TOPOLOGICAL_COLLAPSE":
                # Gestão S5: SL super apertado, confiando na ignição imediata
                if direction == "LONG":
                    sl_price = max(sl_price, pos["entry_price"] - (atr * 1.5))
                    if qdd_f < -0.5: action = "EXIT_QDD_REVERSAL"
                else:
                    sl_price = min(sl_price, pos["entry_price"] + (atr * 1.5))
                    if qdd_f > 0.5: action = "EXIT_QDD_REVERSAL"
                    
            elif setup == "S1_GRAVITATIONAL_SLINGSHOT":
                # S1 confia 100% no PreCognition SL e QTE TP
                pass

            zones[ticket] = {
                "sl": sl_price,
                "tp": tp_price,
                "action": action
            }

        return zones
