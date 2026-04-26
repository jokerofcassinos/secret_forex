import pandas as pd
import numpy as np
from collections import deque
import os

class NeuralMemoryCore:
    def __init__(self, symbol="BTCUSD"):
        self.symbol = symbol
        self.data_path = "Data/Historical/"
        self.ltm = {}  # Long Term Memory (Histórico)
        self.stm = {   # Short Term Memory (Buffer em tempo real)
            "ticks": deque(maxlen=1000),
            "m1_context": deque(maxlen=100)
        }
        self.market_state = "UNKNOWN"

    def load_ltm(self):
        """Carrega a memória de longo prazo do disco."""
        print(f"NEXUS :: Sincronizando LTM para {self.symbol}...")
        try:
            for file in os.listdir(self.data_path):
                if file.startswith(self.symbol) and file.endswith(".parquet"):
                    tf_name = file.split("_")[1].split(".")[0]
                    self.ltm[tf_name] = pd.read_parquet(os.path.join(self.data_path, file))
            print(f"LTM Sincronizada: {list(self.ltm.keys())}")
            return True
        except Exception as e:
            print(f"Erro ao carregar LTM: {e}")
            return False

    def get_neural_snapshot(self):
        """
        Gera um resumo do contexto atual do mercado.
        Isso dá ao bot a 'consciência' do passado imediato.
        """
        snapshot = {
            "timestamp": pd.Timestamp.now(),
            "regime": self._calculate_regime(),
            "volatility": self._get_current_volatility(),
            "trend_alignment": self._check_trend_alignment()
        }
        self.market_state = snapshot
        self._document_state_in_obsidian(snapshot)
        return snapshot

    def _calculate_regime(self):
        # Lógica PhD: Analisar se estamos em tendência, range ou expansão quântica
        if "H4" in self.ltm:
            last_close = self.ltm["H4"]["close"].iloc[-1]
            ma_200 = self.ltm["H4"]["close"].rolling(200).mean().iloc[-1]
            return "BULLISH" if last_close > ma_200 else "BEARISH"
        return "NEUTRAL"

    def _get_current_volatility(self):
        if "M1" in self.ltm:
            return self.ltm["M1"]["close"].pct_change().std()
        return 0

    def _check_trend_alignment(self):
        # Verifica se M15, H1 e H4 estão na mesma direção
        return "ALIGNED" # Placeholder para lógica complexa

    def perform_historical_audit(self):
        """Analisa o histórico para validar a consistência do regime."""
        print("NEXUS :: Iniciando Auditoria Histórica de Contexto...")
        audit_results = []
        if "H1" in self.ltm:
            data = self.ltm["H1"]
            # Simula a percepção da IA nos últimos 50 períodos do histórico
            for i in range(len(data)-50, len(data)):
                window = data.iloc[:i]
                last_price = window["close"].iloc[-1]
                ma_200 = window["close"].rolling(200).mean().iloc[-1]
                regime = "BULLISH" if last_price > ma_200 else "BEARISH"
                audit_results.append(regime)
        
        consistency = (audit_results.count(self.market_state["regime"]) / len(audit_results)) * 100 if audit_results else 0
        print(f"Auditoria Concluída. Confiança no Regime Atual: {consistency:.2f}%")
        return consistency

    def _document_state_in_obsidian(self, state):
        """Registra o estado mental do bot para auditoria em Docs/04_Perfis_Neurais/."""
        log_path = f"Docs/04_Perfis_Neurais/STATE_{self.symbol}.md"
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"# 🧠 ESTADO MENTAL NEURAL: {self.symbol}\n\n")
                f.write(f"- **Data/Hora:** {state['timestamp']}\n")
                f.write(f"- **Regime Detectado:** {state['regime']}\n")
                f.write(f"- **Volatilidade:** {state['volatility']:.6f}\n")
                f.write(f"- **Alinhamento:** {state['trend_alignment']}\n\n")
                f.write("## 📝 Análise CEO\n")
                f.write("Integridade recuperada. Sistema em observação ativa.\n")
        except Exception as e:
            print(f"Erro ao documentar no Obsidian: {e}")

if __name__ == "__main__":
    core = NeuralMemoryCore("BTCUSD")
    if core.load_ltm():
        print(core.get_neural_snapshot())
