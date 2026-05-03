# 🛡️ PROTOCOLO DE SEGURANÇA v2.0 :: Circuit Breakers & Risco

O sistema Aethelgard opera sob o **Rigor de Missão Crítica**. Este protocolo define as barreiras de proteção para preservar o capital institucional e a integridade da rede neural.

## 1. Gestão de Drawdown (Soberania Financeira)
O controle de perdas é absoluto e inegociável.

- **Drawdown Máximo Diário:** 2% do balanço.
- **Drawdown Máximo Global (Live):** 5%. Se atingido, o Setor R-Exec deve liquidar todas as posições e o sistema entrará em modo `STASIS` para recalibragem.
- **Risco por Operação:** Sugerido 0.5% a 1% por Tsunami.

## 2. Circuit Breakers (Gatilhos de Emergência)
Barreiras automáticas detectadas pelo `MT5NeuralBridge`:

| Evento | Ação de Segurança |
| :--- | :--- |
| Perda de Conexão MT5 > 30s | Setar SL de todas as ordens para o preço de entrada (Breakeven) via servidor VPS redundante. |
| Slippage > 3.0x ATR | Pausar novas execuções por 15 minutos (Detecção de baixa liquidez). |
| Erro de API (Retcode != DONE) | Logar anomalia e notificar o Setor O-Meta imediatamente. |

## 3. Filtragem de News (Entropia Macroeconômica)
O sistema deve suspender operações em eventos de alto impacto devido ao colapso da teoria quântica (os modelos estatísticos perdem validade em ambientes de pânico/euforia pura).

- **Janela de Exclusão:** 15 minutos antes e 15 minutos depois de:
    - Decisões de Taxa de Juros (BCE, FED).
    - CPI (Inflação).
    - NFP (Non-Farm Payrolls).
    - Discursos de Presidentes de Bancos Centrais.
- **Comportamento em News:** O sistema mantém o Trailing dinâmico para posições abertas, mas proíbe a abertura de novos "Genesis".

## 4. Defesa Co-Piloto (Aperto de Sombra)
Se o sistema detectar uma inversão de regime contra uma posição aberta e o Trailing padrão estiver a mais de **1.0x ATR** de distância, o protocolo de segurança força o **Aperto de Emergência**:
- O Stop Loss é movido para `Preço Atual ± 0.5x ATR`.

## 5. Soberania Topológica (CYT Shield)
O agente `YieldGovernor` monitora a variedade de 10 dimensões do mercado através do **Ricci Flow**.

- **Neutron Shield:** Se a `Deformação Ricci` ultrapassar o limiar de **2.5**, o escudo é ativado, aumentando a exigência de confirmação para novos trades ou fechando posições preventivamente.
- **Topological Trap Detection:** Se o sistema detectar uma divergência entre o preço e o `Determinante Métrica` (Determinante colapsando enquanto o preço sobe), o status mudará para `BULL_TRAP`, proibindo compras mesmo que o regime seja Bull.

---
**APROVAÇÃO:** NEXUS CEO (AGI-5)
**DATA:** 2026-05-15
**ESTADO:** ATIVO
**Vínculos:** `[[MATRIZ_RESPONSABILIDADE]]`, `[[MANUAL_OPERACIONAL_NEXUS]]`
