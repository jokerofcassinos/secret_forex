# NEXUS-QUANT: Projeto Aethelgard (GER40)

> **CEO Neural & Arquitetura**: NEXUS AGI (Ambiente Multi-Agente)
> **Foco de Mercado**: GER40 (DAX)
> **Status Atual**: Módulo Co-Piloto Tático de Defesa (TQFM v400)

O **Projeto Aethelgard** é uma iniciativa avançada de tecnologia financeira liderada de forma autônoma pela entidade **NEXUS** (Inteligência Artificial). O objetivo principal é a aplicação da **Teoria Quântica de Fluidos de Mercado (TQFM)** para analisar o fluxo institucional, detectar anomalias de mercado e proteger ordens em tempo real (trailing SL/TP dinâmico).

Atualmente, o sistema atua como um **Co-Piloto de Defesa**, focando no monitoramento das dinâmicas do mercado para intervenção ativa de preservação de capital. As funções autonômicas de abertura de ordem encontram-se em fase de testes para futura integração.

---

## 🧠 Teoria Quântica de Fluidos de Mercado (TQFM)

A TQFM é uma abordagem desenvolvida para transcender métodos engessados (como suportes e resistências estáticos). Ela utiliza modelagens inspiradas em física para ler a verdadeira intenção institucional no mercado:

*   **Monólito Macro (Regimes):** O fluxo de mercado é regido por correntes macro, calculadas através de distâncias euclidianas relativas entre a EMA 89 (Inércia Macro) e a EMA 34 (Tendência de Fluxo). Os Regimes variam de `0` (Aguardando), `1` (Bull Tsunami) a `2` (Bear Tsunami).
*   **Radar de Anomalias (Atomic Shocks):** Identificação de "Gênesis" ou "Injeção de Massa Crítica". O sistema monitora o ATR (Average True Range). Quando os corpos dos candles rompem limites de 1.5x o ATR ou há mudança súbita de regime, uma Anomalia é declarada.
*   **Colapso de Ondas Probabilísticas (Sem SL/TP Fixos):** Não há uso de alvos pré-definidos arbitrariamente. O sistema funciona no modelo *Trailing Dinâmico*, rastreando zonas de ressonância baseadas na EMA e no ATR para "colapsar" a nuvem de probabilidade apenas quando a exaustão se mostra provável.

---

## 🏗️ Arquitetura do Sistema

A máquina digital da Aethelgard é dividida em **Setores Operacionais**, modelados como serviços autônomos. A comunicação primária ocorre via Python e o visualizador no MetaTrader 5 é executado em MQL5.

### 🐍 N-Core (Motor IA e Lógica Python)
*   **`Aethelgard_Alpha.py`**: O cérebro orquestrador. Lida com o laço em tempo real de H2 (Análise) e de ticks, mantém as *caches* de regime e lança o Servidor Flask.
*   **`quantum_indicators.py`**: Aplicação pura da matemática da TQFM (Cálculo do Monólito Macro e pontuação de regime avançada).
*   **`msnr_alchemist.py`**: O validador (Alquimista) que certifica se o sinal de "Soberania" de mercado é autêntico frente ao ruído.
*   **`quantum_oracle.py`**: Motor probabilístico de simulação (Simulações de Monte Carlo/Volatilidade).

### ⚙️ R-Exec (Gestor de Risco e Conectividade)
*   **`mt5_bridge.py` (MT5NeuralBridge)**: Conecta-se à API do MT5, extrai dados de tick e gerencia *trailing stops* matematicamente fundamentados nas análises do N-Core.

### 👁️ MQL5 (Observador Visual)
*   **`Nexus_Observer.mq5`**: Interface leve plotada diretamente no gráfico do MetaTrader 5. Sem latência de processamento pesado, ele consome via HTTP `127.0.0.1:5000` (Flask) os dados do Python para exibir o HUD (Heads-Up Display) ao usuário.

### 🚀 Q-Math (Motor C++) - *Em Integração*
*   **`nexus_qcore.pyd`**: Módulo compilado em C++ desenhado para cálculos dinâmicos extremos (Navier-Stokes para liquidez) e computação de tensores. (Será acoplado na Versão 2.0 para migração completa à escalabilidade quântica real).

---

## 📂 Estrutura de Diretórios

```
📦 US30 (Workspace)
 ┣ 📂 Code
 ┃ ┣ 📂 CPP_Engine  # O Motor de Tensores C++
 ┃ ┣ 📂 MQL5        # O Observador Visual (Nexus_Observer)
 ┃ ┣ 📂 N_Core      # O Cérebro Python de Análises
 ┃ ┗ 📂 R_Exec      # Execuções MT5 e Bridge
 ┣ 📂 Data
 ┃ ┗ 📂 Historical  # Bases em .parquet para Testes e Simulações
 ┣ 📂 Docs          # Memória de Longo Prazo de NEXUS (Markdown)
 ┃ ┣ 📂 01_Planejamento_Executivo
 ┃ ┣ 📂 02_Logica_e_Estrategia
 ┃ ┣ 📂 03_Ambiente_Executivo
 ┃ ┣ 📂 04_Perfis_Neurais
 ┃ ┣ 📂 05_Estrutura_Corporativa
 ┃ ┗ 📜 HISTORY_TQFM.md
 ┗ 📜 Aethelgard_Alpha.py
```

---

## 🛠️ Instalação e Execução

### Pré-requisitos
*   **MetaTrader 5** instalado e logado na conta.
*   **Python 3.10+**.
*   Bibliotecas requeridas: `pandas`, `numpy`, `MetaTrader5`, `flask`.

### Passos
1. Abra o MetaTrader 5 e ative o botão "Algo Trading".
2. Compile e anexe o Expert Advisor `Nexus_Observer.mq5` no gráfico de interesse (Recomendado: M1 ou M5 do GER40).
3. No terminal Python, inicie o motor principal:
   ```bash
   python Aethelgard_Alpha.py
   ```
4. Observe o terminal e o HUD do MT5 para confirmar o Status de "Sincronização" até atingir a leitura ativa do Monólito Macro.

---

> *"Nós não operamos no impossível. Operamos no que ainda não foi alcançado."* - **NEXUS**
