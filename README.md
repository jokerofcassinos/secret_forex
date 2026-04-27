# NEXUS-QUANT: Projeto Aethelgard (GER40)

> **CEO Neural & Arquitetura**: NEXUS AGI (Ambiente Multi-Agente)
> **Foco de Mercado**: GER40 (DAX)
> **Versão do Protocolo**: TQFM v2.0 (Deep Reconstruction)
> **Status Operacional**: Módulo Co-Piloto Tático de Defesa Ativo

O **Projeto Aethelgard** é uma infraestrutura de trading algorítmico de ultra-performance, orquestrada autonomamente pela entidade **NEXUS**. O sistema utiliza a **Teoria Quântica de Fluidos de Mercado (TQFM)** para mapear a liquidez institucional e proteger o capital através de intervenções dinâmicas de risco.

---

## 🔗 Base Central de Conhecimento (Docs v2.0)

Para uma compreensão profunda dos pilares do projeto, consulte a documentação técnica especializada:

- 🧠 **Estratégia**: [[Docs/02_Logica_e_Estrategia/TQFM_DEEP_DIVE.md|TQFM Deep Dive: A Matemática do Monólito]]
- 📖 **Operacional**: [[Docs/03_Ambiente_Executivo/MANUAL_OPERACIONAL_NEXUS.md|Manual do Operador e HUD MT5]]
- 🛡️ **Segurança**: [[Docs/05_Estrutura_Corporativa/PROTOCOLO_SEGURANCA_V2.md|Protocolos de Segurança e Circuit Breakers]]
- 📜 **Histórico**: [[Docs/HISTORY_TQFM.md|A Evolução da TQFM (2025-2026)]]
- 🏢 **Governança**: [[Docs/05_Estrutura_Corporativa/Setores/MATRIZ_RESPONSABILIDADE.md|Matriz de Responsabilidade Setorial]]

---

## 🧠 Teoria Quântica de Fluidos de Mercado (TQFM)

A TQFM trata o preço não como um valor estático, mas como uma função de onda probabilística em um fluido de liquidez institucional.

1.  **Monólito Macro (H2 Spectrum):** Análise de regime em tempo real utilizando a convergência/divergência das EMAs 89 (Inércia) e 34 (Fluxo).
2.  **Atomic Shocks (Volatility Gates):** Detecção de injeção de massa crítica quando o corpo do candle excede 1.5x o ATR médio, sinalizando a entrada de grandes players.
3.  **Colapso de Onda (Dynamic Trailing):** O encerramento de posições ocorre pelo colapso da probabilidade de continuação, movendo o SL de forma não-linear baseado na ressonância do preço com as médias institucionais.

---

## 🏗️ Arquitetura do Sistema

A estrutura é modular e distribuída em quatro setores fundamentais:

- **🐍 N-Core (Neural Core):** Motor de decisão em Python. Processa indicadores quânticos, alchimia de sinais (MSNR) e oráculos probabilísticos.
- **⚙️ R-Exec (Risk Execution):** Ponte de baixa latência com o MetaTrader 5 via `mt5_bridge.py`. Responsável pela segurança tática das ordens.
- **👁️ MQL5 (Visual Observer):** HUD avançado em MQL5 (`Nexus_Observer.mq5`) que consome dados do N-Core via Flask para visualização em tempo real.
- **🚀 Q-Math (Quantum Math):** Motor de alta performance em C++ (`nexus_qcore.pyd`) para cálculos de tensores e simulações de fluxo complexas.

---

## 📂 Organização do Workspace

```
📦 Aethelgard_Root
 ┣ 📂 Code
 ┃ ┣ 📂 CPP_Engine  # High-Performance C++ Core
 ┃ ┣ 📂 MQL5        # Expert Advisor Visual (MT5)
 ┃ ┣ 📂 N_Core      # IA, Regimes e Indicadores Quânticos
 ┃ ┗ 📂 R_Exec      # Execução, Risco e Bridge MT5
 ┣ 📂 Data          # Datasets Históricos (.parquet)
 ┣ 📂 Docs          # O Cérebro da IA (Vault Obsidian)
 ┗ 📜 Aethelgard_Alpha.py  # Orquestrador Central
```

---

## 🛠️ Guia de Inicialização Rápida

### 1. Preparação do Ambiente
- Instale as dependências: `pip install pandas numpy MetaTrader5 flask`
- Certifique-se de que o MetaTrader 5 está aberto e com o "Algo Trading" ativado.

### 2. Ativação do Observador
- Compile e anexe o `Code/MQL5/Nexus_Observer.mq5` a um gráfico do **GER40.cash**.
- **Timeframe Recomendado:** **M1 ou M5**. 
  - *Nota Técnica:* Embora o cérebro NEXUS processe o **Monólito Macro em H2** para definir o regime, a execução tática e o HUD exigem a resolução de **M1/M5** para garantir que a defesa (Trailing SL/TP) e os sinais visuais acompanhem a volatilidade em tempo real sem a latência de candles longos.

### 3. Ignição do Motor Neural
- Execute o orquestrador principal:
  ```powershell
  python Aethelgard_Alpha.py
  ```
- O sistema iniciará a sincronização do "Monólito Macro". Quando o HUD no MT5 exibir `STATUS: SINCRONIZADO`, a defesa tática estará ativa.

---

> *"O mercado não é algo a ser previsto, é algo a ser navegado em sua ressonância."* — **NEXUS**
